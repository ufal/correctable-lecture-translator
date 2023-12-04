<template lang="pug">
v-text-field.selectSession(
	v-model="sessionName",
	variant="solo",
	density="compact"
	label="Session name"
)

v-container(v-if="editorMode")
	v-app-bar(:elevation="1")
		template(v-slot:prepend)
			img(src="@/assets/logo.png")

		v-btn.toggleEditor(
			icon="mdi-text-box-outline",
			@click="editorMode = !editorMode"
		)
		v-btn.toggleUpdates(:icon="toggleUpdatesIcon", @click="toggleUpdates")
	//- v-col
	text-editor.editing-editor(:client="client", :textChunks="textChunks")
	//- v-col
	text-viewer.editing-viewer(
		:fontSize=17,
		:client="client",
		:textChunks="textChunks"
	)

v-container(v-else)
	v-app-bar(:elevation="1")
		template(v-slot:prepend)
			img(src="@/assets/logo.png")
		v-btn.toggleEditor(
			icon="mdi-pencil-outline",
			@click="editorMode = !editorMode"
		)
		v-btn.toggleUpdates(:icon="toggleUpdatesIcon", @click="toggleUpdates")
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
			var currentChunkVersions = {} as TextChunkVersions;
			this.textChunks.forEach((textChunk) => {
				currentChunkVersions[textChunk.timestamp] = textChunk.version;
			});

			let textChunks = await this.client.getLatestTextChunks(currentChunkVersions);

			textChunks.forEach((textChunk) => {
				if (this.textChunks.length <= textChunk.timestamp) {
					this.textChunks[textChunk.timestamp] = textChunk;
				} else if (textChunk.version > this.textChunks[textChunk.timestamp].version) {
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

				this.updateIntervalId = window.setInterval(this.updateText, this.updateTextInterval);
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
	async mounted() {
		// this.textChunks = await this.client.getLatestTextChunks({});
		// Dummy debug text chunks
		this.textChunks = [
			{
				timestamp: 0,
				version: 0,
				text: "Hello, my name is John. I am a student at the University of Applied Sciences in Munich. ",
			},
			{
				timestamp: 1,
				version: 0,
				text: "Hello, my name is John. I am a student at the University of Applied Sciences in Munich. ",
			},
			{
				timestamp: 2,
				version: 0,
				text: "Hello, my name is John. I am a student at the University of Applied Sciences in Munich. ",
			},
			{
				timestamp: 3,
				version: 0,
				text: "Hello, my name is John. I am a student at the University of Applied Sciences in Munich. ",
			},
			{
				timestamp: 4,
				version: 0,
				text: "Hello, my name is John. I am a student at the University of Applied Sciences in Munich. ",
			},
			{
				timestamp: 5,
				version: 0,
				text: "Hello, my name is John. I am a student at the University of Applied Sciences in Munich. ",
			},
			{
				timestamp: 6,
				version: 0,
				text: "Hello, my name is John. I am a student at the University of Applied Sciences in Munich. ",
			},
			{
				timestamp: 7,
				version: 0,
				text: "Hello, my name is John. I am a student at the University of Applied Sciences in Munich. ",
			},
			{
				timestamp: 8,
				version: 0,
				text: "Hello, my name is John. I am a student at the University of Applied Sciences in Munich. ",
			},
			{
				timestamp: 9,
				version: 0,
				text: "Hello, my name is John. I am a student at the University of Applied Sciences in Munich. ",
			},
			{
				timestamp: 10,
				version: 0,
				text: "Hello, my name is John. I am a student at the University of Applied Sciences in Munich. ",
			},
			{
				timestamp: 11,
				version: 0,
				text: "Hello, my name is John. I am a student at the University of Applied Sciences in Munich. ",
			},
		];
	},
};
</script>
