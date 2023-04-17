<template lang="pug">
v-card.list(title="Active sessions")
	v-list-item.item(
		v-for="sessionName in activeSessions",
	) {{  sessionName  }}
		template(v-slot:append)
			v-btn(
            	icon="mdi-close",
				size="x-small",
				variant="plain",
				@click="endSession(sessionName)"
			)
</template>

<script lang="ts">
import type { PropType } from "vue";
import AsrClient from "@/utils/client";
import "@/styles/sessionList.scss";

export default {
	name: "session-list-item",
	props: {
		client: {
			type: Object as PropType<AsrClient>,
			required: true,
		},
		activeSessions: {
			type: Object as PropType<string[]>,
			required: true,
		},
	},
	methods: {
		async endSession(sessionName: string) {
			await this.client.setSessionId(sessionName);
			await this.client.endSession();
			this.$emit("update-sessions");
		},
	},
};
</script>
