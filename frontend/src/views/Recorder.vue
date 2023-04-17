<template lang="pug">
session-list(:client="client", :activeSessions="activeSessions" @update-sessions="getSessions")

v-text-field.idInput(
	label="Current session id",
	v-model="sessionName",
	@click:append-inner="createSession",
	append-inner-icon="mdi-check",
	variant="solo",
)

audio-recorder(:asrClient="client", :sampleRate="sampleRate")
</template>

<script lang="ts">
import AsrClient from "@/utils/client";
import AudioRecorder from "@/components/AudioRecorder.vue";
import SessionList from "@/components/SessionList.vue";
import "@/styles/recorder.scss";

export default {
	data() {
		return {
			client: new AsrClient({}),
			sampleRate: 16000,
			activeSessions: [""],
			sessionName: "",
		};
	},
	mounted() {
		this.getSessions();
	},
	methods: {
		async getSessions() {
			this.activeSessions = await this.client.getActiveSessions();
			this.sessionName = this.client.sessionId;
		},
		async createSession() {
			await this.client.setSessionId(this.sessionName);
			await this.client.createSession()
			this.getSessions();
		},
	},
};
</script>
