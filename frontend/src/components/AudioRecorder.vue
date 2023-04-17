<template lang="pug">
v-card-text Record:
	v-btn.recordButton(@click="toggleRecording", :icon="recordingIcon")
</template>

<script lang="ts">
import AsrClient from "@/utils/client";

export default {
	name: "audio-recorder",
	props: {
		asrClient: { type: AsrClient, required: true },
		sampleRate: { type: Number, required: true },
	},
	data() {
		return {
			context: {} as AudioContext,
			source: {} as MediaStreamAudioSourceNode,
			microphone: {} as MediaStream,
			recorder: {} as AudioWorkletNode,
			timestamp: 0,
			recording: false,
			recordingIcon: "mdi-microphone",
		};
	},
	methods: {
		async createAudioContext() {
			this.context = new AudioContext({
				latencyHint: "interactive",
				sampleRate: this.sampleRate, // default: 16000
			});
		},
		async getRecorder() {
			await this.context.audioWorklet.addModule("/recorder.worklet.js");
			this.recorder = new AudioWorkletNode(
				this.context,
				"recorder.worklet"
			);
		},
		async getMicrophone() {
			this.microphone = await navigator.mediaDevices.getUserMedia({
				audio: true,
			});
		},
		async createSource() {
			this.source = this.context.createMediaStreamSource(this.microphone);
			this.source
				.connect(this.recorder)
				.connect(this.context.destination);
		},
		async submitAudioChunk(audioEvent: { data: Float32Array }) {
			const res = await this.asrClient.submitAudioChunk({
				timestamp: this.timestamp++,
				chunk: audioEvent.data,
			});
			if (!res.success) {
				console.error("Error while submitting audio chunk:");
				console.error(res.message);
			}
		},
		async startRecording() {
			await this.createAudioContext();
			await this.getRecorder();
			await this.getMicrophone();
			await this.createSource();

			this.recorder.port.onmessage = this.submitAudioChunk;
			this.recording = true;

			console.info("Started recording.");
		},
		async stopRecording() {
			this.source.disconnect();
			this.recorder.disconnect();
			this.context.close();
			this.recording = false;

			console.info("Stopped recording.");
		},
		async toggleRecording() {
			if (this.recording) {
				await this.stopRecording();
				this.recordingIcon = "mdi-microphone";
			} else {
				await this.startRecording();
				this.recordingIcon = "mdi-stop";
			}
		},
	},
};
</script>
