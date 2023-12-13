<template lang="pug">
protected(v-if="!auth.loggedIn", :auth="auth")
.container(v-else)
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
import Protected from "@/components/Protected.vue";
import AsrClient from "@/utils/client";
import AudioRecorder from "@/components/AudioRecorder.vue";
import SessionList from "@/components/SessionList.vue";
import "@/styles/recording.scss";

export default {
	data() {
		return {
			client: new AsrClient({}),
			sampleRate: 16000,
			activeSessions: [""],
			sessionName: "",
			auth: { loggedIn: false },
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
			await this.client.createSession();
			this.getSessions();
		},
	},
};
</script>
