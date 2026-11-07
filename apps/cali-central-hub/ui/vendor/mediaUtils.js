/**
 * Media Utilities - Audio and Video streaming helpers for Gemini Live API
 * Handles media capture, processing, and playback
 */

/**
 * Audio Streamer - Captures and streams microphone audio
 */
class AudioStreamer {
  constructor(geminiClient) {
    this.client = geminiClient;
    this.audioContext = null;
    this.audioWorklet = null;
    this.mediaStream = null;
    this.isStreaming = false;
    this.sampleRate = 16000; // Gemini requires 16kHz
  }

  /**
   * Start streaming audio from microphone
   * @param {string} deviceId - Optional device ID for specific microphone
   */
  async start(deviceId = null) {
    try {
      // Build audio constraints
      const audioConstraints = {
        sampleRate: this.sampleRate,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      };

      // Add device ID if specified
      if (deviceId) {
        audioConstraints.deviceId = { exact: deviceId };
      }

      // Get microphone access
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: audioConstraints,
      });

      // Create audio context at 16kHz
      this.audioContext = new (window.AudioContext ||
        window.webkitAudioContext)({
        sampleRate: this.sampleRate,
      });

      // Load the audio worklet module
      await this.audioContext.audioWorklet.addModule(
        "audio-processors/capture.worklet.js"
      );

      // stop() may have already run while the addModule() await above was
      // pending (e.g. the Live Vision overlay was closed mid-connect) --
      // nulling this.audioContext. Constructing AudioWorkletNode with a null
      // context throws "parameter 1 is not of type 'BaseAudioContext'"
      // instead of a clean, catchable abort.
      if (!this.audioContext) {
        console.warn("AudioStreamer.start() aborted: stopped mid-startup");
        return false;
      }

      // Create the audio worklet node
      this.audioWorklet = new AudioWorkletNode(
        this.audioContext,
        "audio-capture-processor"
      );

      // Set up message handling from the worklet
      this.audioWorklet.port.onmessage = (event) => {
        if (!this.isStreaming) return;

        if (event.data.type === "audio") {
          const inputData = event.data.data;
          const pcmData = this.convertToPCM16(inputData);
          const base64Audio = this.arrayBufferToBase64(pcmData);

          // Send to Gemini
          if (this.client && this.client.connected) {
            if (!this._loggedFirstChunk) {
              this._loggedFirstChunk = true;
              console.log("audio: first mic chunk sent to live vision socket");
            }
            this.client.sendAudioMessage(base64Audio);
          } else if (!this._loggedDropped) {
            this._loggedDropped = true;
            console.warn("audio: dropping mic chunk, no connected client yet");
          }
        }
      };

      // Connect the audio graph
      const source = this.audioContext.createMediaStreamSource(
        this.mediaStream
      );
      source.connect(this.audioWorklet);

      this.isStreaming = true;
      console.log("🎤 Audio streaming started");
      return true;
    } catch (error) {
      console.error("Failed to start audio streaming:", error);
      throw error;
    }
  }

  /**
   * Stop audio streaming
   */
  stop() {
    this.isStreaming = false;

    if (this.audioWorklet) {
      this.audioWorklet.disconnect();
      this.audioWorklet.port.close();
      this.audioWorklet = null;
    }

    if (this.audioContext) {
      this.audioContext.close();
      this.audioContext = null;
    }

    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((track) => track.stop());
      this.mediaStream = null;
    }

    console.log("🛑 Audio streaming stopped");
  }

  /**
   * Convert Float32Array to PCM16 Int16Array
   */
  convertToPCM16(float32Array) {
    const int16Array = new Int16Array(float32Array.length);
    for (let i = 0; i < float32Array.length; i++) {
      const sample = Math.max(-1, Math.min(1, float32Array[i]));
      int16Array[i] = sample * 0x7fff;
    }
    return int16Array.buffer;
  }

  /**
   * Convert ArrayBuffer to base64
   */
  arrayBufferToBase64(buffer) {
    const bytes = new Uint8Array(buffer);
    let binary = "";
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return window.btoa(binary);
  }
}

/**
 * Base Video Capture - Shared functionality for video/screen capture
 */
class BaseVideoCapture {
  constructor(geminiClient) {
    this.client = geminiClient;
    this.video = null;
    this.canvas = null;
    this.ctx = null;
    this.mediaStream = null;
    this.isStreaming = false;
    this.captureInterval = null;
    this.fps = 1; // Default 1 frame per second
    this.quality = 0.8; // Default JPEG quality
  }

  /**
   * Initialize canvas and video elements
   * @param {HTMLElement} [container] - if given, the video element is
   *   appended here BEFORE srcObject/play() are set up. Some mobile WebView
   *   engines only properly render a stream that was already attached to
   *   the document when playback started -- attaching it later (after
   *   waitForVideoReady()'s play() call) can leave frame capture working
   *   (canvas keeps drawing fine) while nothing visibly renders on screen.
   */
  initializeElements(width, height, container) {
    // Create video element
    this.video = document.createElement("video");
    this.video.autoplay = true;
    this.video.playsInline = true;
    this.video.muted = true;
    if (container) {
      container.innerHTML = "";
      container.appendChild(this.video);
    }
    this.video.srcObject = this.mediaStream;

    // Create canvas for frame capture
    this.canvas = document.createElement("canvas");
    this.canvas.width = width;
    this.canvas.height = height;
    this.ctx = this.canvas.getContext("2d");
  }

  /**
   * Wait for video to be ready and start playing
   */
  async waitForVideoReady() {
    await new Promise((resolve) => {
      this.video.onloadedmetadata = resolve;
    });
    this.video.play();
  }

  /**
   * Start capturing and sending frames
   */
  startCapturing() {
    const captureFrame = () => {
      if (!this.isStreaming) return;

      // Draw current frame to canvas
      this.ctx.drawImage(
        this.video,
        0,
        0,
        this.canvas.width,
        this.canvas.height
      );

      // Convert to JPEG and send
      this.canvas.toBlob(
        (blob) => {
          if (!blob) return;

          const reader = new FileReader();
          reader.onloadend = () => {
            const base64 = reader.result.split(",")[1];
            if (this.client && this.client.connected) {
              this.client.sendImageMessage(base64, "image/jpeg");
            }
          };
          reader.readAsDataURL(blob);
        },
        "image/jpeg",
        this.quality
      );
    };

    // Start interval
    this.captureInterval = setInterval(captureFrame, 1000 / this.fps);
  }

  /**
   * Stop capturing
   */
  stop() {
    this.isStreaming = false;

    if (this.captureInterval) {
      clearInterval(this.captureInterval);
      this.captureInterval = null;
    }

    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((track) => track.stop());
      this.mediaStream = null;
    }

    if (this.video) {
      this.video.srcObject = null;
      this.video = null;
    }

    this.canvas = null;
    this.ctx = null;
  }

  /**
   * Take a single snapshot
   */
  takeSnapshot() {
    if (!this.video || !this.canvas) {
      throw new Error("Video not initialized");
    }

    this.ctx.drawImage(
      this.video,
      0,
      0,
      this.canvas.width,
      this.canvas.height
    );
    return this.canvas.toDataURL("image/jpeg", this.quality);
  }

  /**
   * Get the video element for preview
   */
  getVideoElement() {
    return this.video;
  }
}

/**
 * Video Streamer - Captures and streams camera video
 */
class VideoStreamer extends BaseVideoCapture {
  /**
   * Start video streaming from camera
   * @param {Object} options - { fps: number, width: number, height: number, facingMode: string, quality: number, deviceId: string }
   */
  async start(options = {}) {
    try {
      const {
        fps = 1,
        width = 640,
        height = 480,
        facingMode = "user", // 'user' for front camera, 'environment' for back
        quality = 0.8,
        deviceId = null,
        container = null,
      } = options;

      this.fps = fps;
      this.quality = quality;

      // Build video constraints
      const videoConstraints = {
        width: { ideal: width },
        height: { ideal: height },
      };

      // Add device ID if specified, otherwise use facingMode
      if (deviceId) {
        videoConstraints.deviceId = { exact: deviceId };
      } else {
        videoConstraints.facingMode = facingMode;
      }

      // Get camera access
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        video: videoConstraints,
      });

      // Initialize video and canvas elements
      this.initializeElements(width, height, container);

      // Wait for video to be ready
      await this.waitForVideoReady();

      // Start capturing frames
      this.isStreaming = true;
      this.startCapturing();

      console.log("📹 Camera streaming started at", fps, "fps");
      return this.video; // Return video element for preview
    } catch (error) {
      console.error("Failed to start camera streaming:", error);
      throw error;
    }
  }

  stop() {
    super.stop();
    console.log("🛑 Camera streaming stopped");
  }
}

/**
 * Screen Capture - Captures and streams screen/window
 */
class ScreenCapture extends BaseVideoCapture {
  /**
   * Start screen capture
   * @param {Object} options - { fps: number, width: number, height: number, quality: number }
   */
  async start(options = {}) {
    try {
      const {
        fps = 1,
        width = 1280,
        height = 720,
        quality = 0.7,
        container = null
      } = options;

      this.fps = fps;
      this.quality = quality;

      // Get screen capture permission
      this.mediaStream = await navigator.mediaDevices.getDisplayMedia({
        video: {
          width: { ideal: width },
          height: { ideal: height },
        },
        audio: false,
      });

      // Initialize video and canvas elements
      this.initializeElements(width, height, container);

      // Wait for video to be ready
      await this.waitForVideoReady();

      // Start capturing frames
      this.isStreaming = true;
      this.startCapturing();

      // Handle stream end (user stops sharing)
      this.mediaStream.getVideoTracks()[0].onended = () => {
        console.log("User stopped screen sharing");
        this.stop();
      };

      console.log("🖥️ Screen capture started at", fps, "fps");
      return this.video; // Return video element for preview
    } catch (error) {
      console.error("Failed to start screen capture:", error);
      throw error;
    }
  }

  stop() {
    super.stop();
    console.log("🛑 Screen capture stopped");
  }
}

/**
 * Audio Player - Plays audio responses from Gemini
 */
class AudioPlayer {
  constructor() {
    this.audioContext = null;
    this.workletNode = null;
    this.gainNode = null;
    this.isInitialized = false;
    this.volume = 1.0;
    this._initializing = null;
    this._playTail = Promise.resolve();
    this._destroyed = false;
    this.sampleRate = 24000; // Gemini outputs at 24kHz
  }

  /**
   * Initialize the audio player
   */
  init() {
    if (this._destroyed) return Promise.reject(new Error('Audio player closed'));
    if (this.isInitialized) return Promise.resolve();
    if (!this._initializing) {
      this._initializing = this._initialize().finally(() => { this._initializing = null; });
    }
    return this._initializing;
  }

  async _initialize() {

    try {
      // Create audio context at 24kHz to match Gemini
      this.audioContext = new (window.AudioContext ||
        window.webkitAudioContext)({
        sampleRate: this.sampleRate,
      });

      const context = this.audioContext;
      // Load the audio worklet from external file
      await this.audioContext.audioWorklet.addModule(
        "audio-processors/playback.worklet.js"
      );

      if (this._destroyed || this.audioContext !== context) throw new Error('Audio player closed');
      // Create worklet node
      this.workletNode = new AudioWorkletNode(
        this.audioContext,
        "pcm-processor"
      );

      // Create gain node for volume control
      this.gainNode = this.audioContext.createGain();
      this.gainNode.gain.value = this.volume;

      // Connect nodes
      this.workletNode.connect(this.gainNode);
      this.gainNode.connect(this.audioContext.destination);

      this.isInitialized = true;
      console.log("🔊 Audio player initialized");
    } catch (error) {
      console.error("Failed to initialize audio player:", error);
      throw error;
    }
  }

  /**
   * Play audio chunk from base64 PCM
   */
  play(base64Audio) {
    const next = this._playTail.catch(() => {}).then(() => this._playChunk(base64Audio));
    this._playTail = next;
    return next;
  }

  async _playChunk(base64Audio) {
    if (this._destroyed) return;
    if (!this.isInitialized) {
      await this.init();
    }

    try {
      // Resume audio context if suspended
      if (this.audioContext.state === "suspended") {
        await this.audioContext.resume();
      }

      // Efficient base64 → binary decode
      const binaryString = atob(base64Audio);
      const len = binaryString.length;
      const bytes = new Uint8Array(len);
      for (let i = 0; i < len; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }

      // Convert PCM16 LE to Float32
      const inputArray = new Int16Array(bytes.buffer);
      const float32Data = new Float32Array(inputArray.length);
      for (let i = 0; i < inputArray.length; i++) {
        float32Data[i] = inputArray[i] / 32768;
      }

      // Send to worklet for playback
      this.workletNode.port.postMessage(float32Data);
    } catch (error) {
      console.error("Error playing audio chunk:", error);
      throw error;
    }
  }

  /**
   * Interrupt current playback
   */
  interrupt() {
    if (this.workletNode) {
      this.workletNode.port.postMessage("interrupt");
    }
  }

  /**
   * Set volume (0.0 to 1.0)
   */
  setVolume(volume) {
    this.volume = Math.max(0, Math.min(1, volume));
    if (this.gainNode) {
      this.gainNode.gain.value = this.volume;
    }
  }

  /**
   * Clean up resources
   */
  destroy() {
    this._destroyed = true;
    if (this.workletNode) { this.workletNode.disconnect(); this.workletNode = null; }
    if (this.gainNode) { this.gainNode.disconnect(); this.gainNode = null; }
    if (this.audioContext) {
      this.audioContext.close().catch(() => {});
      this.audioContext = null;
    }
    this.isInitialized = false;
  }
}

// ===== VAD (voice activity detection) =====

class VADStreamer {
  constructor(onUtterance) {
    this.onUtterance = onUtterance;
    this.audioContext = null;
    this.vadWorklet = null;
    this.mediaStream = null;
    this.isActive = false;
    this.sampleRate = 16000;
    this.isSpeaking = false;
    this.onStateChange = null;
    this.onLevel = null;
  }

  async start(deviceId, vadConfig) {
    if (this.isActive) return;
    try {
      var constraints = {
        audio: {
          sampleRate: this.sampleRate,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      };
      if (deviceId) {
        constraints.audio.deviceId = { exact: deviceId };
      }

      this.mediaStream = await navigator.mediaDevices.getUserMedia(constraints);
      var AC = window.AudioContext || window.webkitAudioContext;
      this.audioContext = new AC({ sampleRate: this.sampleRate });

      await this.audioContext.audioWorklet.addModule(
        'audio-processors/vad.worklet.js'
      );

      this.vadWorklet = new AudioWorkletNode(this.audioContext, 'vad-processor');

      if (vadConfig) {
        this.vadWorklet.port.postMessage({ type: 'config', ...vadConfig });
      }

      var self = this;
      this.vadWorklet.port.onmessage = function (event) {
        var msg = event.data;
        switch (msg.type) {
          case 'speech_start':
            self.isSpeaking = true;
            break;
          case 'speech_end':
            self.isSpeaking = false;
            if (self.onUtterance && msg.flt) {
              self.onUtterance(msg.flt, msg.durationMs);
            }
            break;
          case 'vad_state':
            if (self.onStateChange) {
              self.onStateChange(msg.state);
            }
            break;
          case 'level':
            if (self.onLevel) {
              self.onLevel(msg.rms);
            }
            break;
        }
      };

      var source = this.audioContext.createMediaStreamSource(this.mediaStream);
      source.connect(this.vadWorklet);

      this.isActive = true;
      console.log('VAD streaming started');
      return true;
    } catch (error) {
      console.error('Failed to start VAD streaming:', error);
      this.stop();
      throw error;
    }
  }

  configure(config) {
    if (this.vadWorklet) {
      this.vadWorklet.port.postMessage({ type: 'config', ...config });
    }
  }

  pause() {
    if (this.vadWorklet) {
      this.vadWorklet.port.postMessage({ type: 'pause' });
    }
  }

  resume() {
    if (this.vadWorklet) {
      this.vadWorklet.port.postMessage({ type: 'resume' });
    }
  }

  stop() {
    this.isActive = false;
    this.isSpeaking = false;

    if (this.vadWorklet) {
      try { this.vadWorklet.disconnect(); } catch (_) {}
      try { this.vadWorklet.port.close(); } catch (_) {}
      this.vadWorklet = null;
    }

    if (this.audioContext) {
      try { this.audioContext.close(); } catch (_) {}
      this.audioContext = null;
    }

    if (this.mediaStream) {
      var tracks = this.mediaStream.getTracks();
      for (var i = 0; i < tracks.length; i++) {
        tracks[i].stop();
      }
      this.mediaStream = null;
    }

    console.log('VAD streaming stopped');
  }
}

// Exposed as globals for the new UI (js/vision.js). Ported from webapp/ 2026-09-25.
window.VideoStreamer = VideoStreamer; window.AudioStreamer = AudioStreamer; window.AudioPlayer = AudioPlayer;
