<template lang="pug">

//- v-text-field.selectSession(
//- 	v-model="sessionName",
//- 	variant="solo",
//- 	density="compact"
//- 	label="Session name"
//- 	id="selectSession"
//- 	flat
//- )

v-container.editor(v-if="editorMode")
	v-app-bar(:elevation="0")
		template(v-slot:prepend)
			//- img(src="@/assets/logo.png")
			.title Coletra - editor
		v-text-field.selectSession(
				v-model="sessionName",
				variant="solo",
				density="compact"
				label="Session name"
				id="selectSession"
				flat
			)
		v-btn.toggleUpdates(:icon="toggleUpdatesIcon", :color="toggleUpdatesColor", @click="toggleUpdates")
		v-btn.toggleEditor(
			icon="mdi-text-box-outline",
			@click="editorMode = !editorMode"
		)
	//- v-col
	text-editor.editing-editor(:client="client", :textChunks="textChunks")
	//- v-col
	br
	//- div.editing-viewer-overlay
	text-viewer.editing-viewer(
		:fontSize=17,
		:client="client",
		:textChunks="textChunks"
	)

v-container.viewer(v-else)
	v-app-bar(:elevation="0")
		template(v-slot:prepend)
			//- img(src="@/assets/logo.png")
			.title Coletra - viewer
		v-text-field.selectSession(
			v-model="sessionName",
			variant="solo",
			density="compact"
			label="Session name"
			id="selectSession"
			flat
		)
		v-btn.toggleUpdates(:icon="toggleUpdatesIcon", :color="toggleUpdatesColor", @click="toggleUpdates")
		v-btn.toggleEditor(
			icon="mdi-pencil-outline",
			@click="editorMode = !editorMode"
		)
	text-viewer(:fontSize=42, :client="client", :textChunks="textChunks")

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
			editorMode: true,
			toggleUpdatesColor: "#286983",
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

			if (!this.editorMode) {
				window.scroll({
					top: document.body.scrollHeight,
					behavior: "smooth",
				});
			}
		},

		toggleUpdates() {
			if (!this.updateIntervalId) {
				this.client.setSessionId(this.sessionName);

				this.updateIntervalId = window.setInterval(this.updateText, this.updateTextInterval);
				this.toggleUpdatesIcon = "mdi-pause";
				this.toggleUpdatesColor = "#ea9d34";
				console.info("Started updating text.");
			} else {
				window.clearInterval(this.updateIntervalId);
				this.updateIntervalId = 0;
				this.toggleUpdatesIcon = "mdi-play";
				this.toggleUpdatesColor = "#286983";
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
			{
				timestamp: 12,
				version: 0,
				text: "Hello, my name is John. I am a student at the University of Applied Sciences in Munich. Hello, my name is John. I am a student at the University of Applied Sciences in Munich. Hello, my name is John. I am a student at the University of Applied Sciences in Munich. Hello, my name is John. I am a student at the University of Applied Sciences in Munich.  ",
			},
			{
				timestamp: 13,
				version: 0,
				text: "Hello, my name is John. I am a student at the University of Applied Sciences in Munich. ",
			},
			{
				timestamp: 14,
				version: 0,
				text: "Hello, my name is John. I am a student at the University of Applied Sciences in Munich. Hello, my name is John. I am a student at the University of Applied Sciences in Munich. Hello, my name is John. I am a student at the University of Applied Sciences in Munich. ",
			},
			{
				timestamp: 15,
				version: 0,
				text: "Hello, my name is John. I am a student at the University of Applied Sciences in Munich. Hello, my name is John. I am a student at the University of Applied Sciences in Munich. Hello, my name is John. I am a student at the University of Applied Sciences in Munich. ",
			},
			{
				timestamp: 16,
				version: 0,
				text: "Hello, my name is John. I am a student at the University of Applied Sciences in Munich. Hello, my name is John. I am a student at the University of Applied Sciences in Munich. Hello, my name is John. I am a student at the University of Applied Sciences in Munich. ",
			},
			{
				timestamp: 17,
				version: 0,
				text: "Hello, my name is John. I am a student at the University of Applied Sciences in Munich. Hello, my name is John. I am a student at the University of Applied Sciences in Munich. Hello, my name is John. I am a student at the University of Applied Sciences in Munich. ",
			},
		];
	},
};
</script>
