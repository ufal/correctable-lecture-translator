<template lang="pug">
v-text-field.selectSession(
	v-model="sessionName",
	variant="solo",
	density="compact"
)

v-container
	v-row(v-if="editorMode")
		v-btn.toggleUpdates(:icon="toggleUpdatesIcon", @click="toggleUpdates")
		v-btn.toggleEditor(
			icon="mdi-text-box-outline",
			@click="editorMode = !editorMode"
		)
		v-col
			text-editor.editing(:client="client", :textChunks="textChunks")
		v-col
			text-viewer.editing(
				:fontSize=17,
				:client="client",
				:textChunks="textChunks"
			)
	v-row(v-else)
		v-btn.toggleUpdates(:icon="toggleUpdatesIcon", @click="toggleUpdates")
		v-btn.toggleEditor(
			icon="mdi-pencil-outline",
			@click="editorMode = !editorMode"
		)
		text-viewer.viewing(:fontSize=42, :client="client", :textChunks="textChunks")
</template>

<script lang="ts">
import "@/styles/textViewer.scss";
import AsrClient from "@/utils/client";
import { TextChunk, TextChunkVersions } from "@/utils/chunk";
import TextViewer from "@/components/TextViewer.vue";
import TextEditor from "@/components/TextEditor.vue";

export default {
	data() {
		return {
			client: new AsrClient({}),
			textChunks: [] as TextChunk[],
			sessionName: "default",
			updateTextInterval: 1000,
			updateIntervalId: 0,
			toggleUpdatesIcon: "mdi-play",
			editorMode: false,
		};
	},

	methods: {
		async updateText() {
			var currentChunkCersions = {} as TextChunkVersions;
			this.textChunks.forEach((textChunk) => {
				currentChunkCersions[textChunk.timestamp] = textChunk.version;
			});

			let textChunks = await this.client.getLatestTextChunks(
				currentChunkCersions
			);

			textChunks.forEach((textChunk) => {
				if (this.textChunks.length <= textChunk.timestamp) {
					this.textChunks[textChunk.timestamp] = textChunk;
				} else if (
					textChunk.version >
					this.textChunks[textChunk.timestamp].version
				) {
					this.textChunks[textChunk.timestamp] = textChunk;
				}
			});

			window.scroll({
				top: document.body.scrollHeight,
				behavior: "smooth",
			});
		},

		toggleUpdates() {
			if (!this.updateIntervalId) {
				this.client.setSessionId(this.sessionName);

				this.updateIntervalId = window.setInterval(
					this.updateText,
					this.updateTextInterval
				);
				this.toggleUpdatesIcon = "mdi-pause";
				console.info("Started updating text.");
			} else {
				window.clearInterval(this.updateIntervalId);
				this.updateIntervalId = 0;
				this.toggleUpdatesIcon = "mdi-play";
				console.info("Stopped updating text.");
			}
		},
	},
	// async mounted() {
		// this.textChunks = await this.client.getLatestTextChunks({});
		// Dummy debug text chunks
		// this.textChunks = [
		// 	{
		// 		timestamp: 0,
		// 		version: 0,
		// 		text: "Hello, my name is John. I am a student at the University of Applied Sciences in Munich. It is not a nice place to live but it is a nice place to study. Lorem Ipsum, sometimes referred to as lipsum, is the placeholder text used in design when creating content. It helps designers plan out where the content will sit, without needing to wait for the content to be written and approved.",
		// 	},
		// 	{
		// 		timestamp: 1,
		// 		version: 0,
		// 		text: "Hello, my name is John. I am a student at the University of Applied Sciences in Munich. It is not a nice place to live but it is a nice place to study. Lorem Ipsum, sometimes referred to as lipsum, is the placeholder text used in design when creating content. It helps designers plan out where the content will sit, without needing to wait for the content to be written and approved.",
		// 	},
		// 	{
		// 		timestamp: 2,
		// 		version: 0,
		// 		text: "Hello, my name is John. I am a student at the University of Applied Sciences in Munich. It is not a nice place to live but it is a nice place to study. Lorem Ipsum, sometimes referred to as lipsum, is the placeholder text used in design when creating content. It helps designers plan out where the content will sit, without needing to wait for the content to be written and approved.",
		// 	},
		// 	{
		// 		timestamp: 3,
		// 		version: 0,
		// 		text: "Hello, my name is John. I am a student at the University of Applied Sciences in Munich. It is not a nice place to live but it is a nice place to study. Lorem Ipsum, sometimes referred to as lipsum, is the placeholder text used in design when creating content. It helps designers plan out where the content will sit, without needing to wait for the content to be written and approved.",
		// 	},
		// 	{
		// 		timestamp: 4,
		// 		version: 0,
		// 		text: "Hello, my name is John. I am a student at the University of Applied Sciences in Munich. It is not a nice place to live but it is a nice place to study. Lorem Ipsum, sometimes referred to as lipsum, is the placeholder text used in design when creating content. It helps designers plan out where the content will sit, without needing to wait for the content to be written and approved.",
		// 	},
		// 	{
		// 		timestamp: 5,
		// 		version: 0,
		// 		text: "Hello, my name is John. I am a student at the University of Applied Sciences in Munich. It is not a nice place to live but it is a nice place to study. Lorem Ipsum, sometimes referred to as lipsum, is the placeholder text used in design when creating content. It helps designers plan out where the content will sit, without needing to wait for the content to be written and approved.",
		// 	},
		// 	{
		// 		timestamp: 6,
		// 		version: 0,
		// 		text: "Hello, my name is John. I am a student at the University of Applied Sciences in Munich. It is not a nice place to live but it is a nice place to study. Lorem Ipsum, sometimes referred to as lipsum, is the placeholder text used in design when creating content. It helps designers plan out where the content will sit, without needing to wait for the content to be written and approved.",
		// 	},
		// 	{
		// 		timestamp: 7,
		// 		version: 0,
		// 		text: "Hello, my name is John. I am a student at the University of Applied Sciences in Munich. It is not a nice place to live but it is a nice place to study. Lorem Ipsum, sometimes referred to as lipsum, is the placeholder text used in design when creating content. It helps designers plan out where the content will sit, without needing to wait for the content to be written and approved.",
		// 	},
		// ];
	// },
};
</script>
