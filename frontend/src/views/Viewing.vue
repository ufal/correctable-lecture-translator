<template lang="pug">

v-app-bar#appBar(:elevation="0")
	template(v-slot:prepend)
		//- img(src="@/assets/logo.png")
		v-btn.toggleEditor(
			icon="mdi-translate",
			@click="editorMode = !editorMode"
		)
		.title Coletra
		v-divider.logoSpacer(vertical, inset, thickness="2", length="40")
		.v-btn(@click="editorMode = false").menuBtn Viewer
		.v-btn(@click="editorMode = true").menuBtn.active Editor
	v-text-field.selectSession(
			v-model="sessionName",
			variant="solo",
			density="compact"
			label="Session name"
			id="selectSession"
			flat
		)
	v-btn.toggleUpdates(:icon="toggleUpdatesIcon", :color="toggleUpdatesColor", @click="toggleUpdates")

v-container.editor(v-if="editorMode")
	dictionary(:client="client")
	text-editor.editing-editor(:client="client", :textChunks="textChunks")
	br
	text-viewer.editing-viewer(
		:client="client",
		:textChunks="textChunks"
	)

v-container.viewer(v-else)
	text-viewer.viewing-viewer(:client="client", :textChunks="textChunks")

</template>

<script lang="ts">
import "@/styles/viewing.scss";
import AsrClient from "@/utils/client";
import { TextChunk, TextChunkVersions } from "@/utils/chunk";
import TextViewer from "@/components/TextViewer.vue";
import TextEditor from "@/components/TextEditor.vue";
import Dictionary from "@/components/Dictionary.vue";

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
			toggleUpdatesColor: "#575279",
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
		var btns = document.getElementsByClassName("menuBtn");
		for (var i = 0; i < btns.length; i++) {
			btns[i].addEventListener("click", function () {
				var current = document.getElementsByClassName("active");
				if (current.length > 0) {
					current[0].className = current[0].className.replace(" active", "");
				}
				// @ts-ignore
				this.className += " active";
			});
		}

		document.onscroll = () => {
			let appBar = document.getElementById("appBar");
			if (window.scrollY > 10) {
				console.log("add shadow");
				if (!appBar?.classList.contains("app-bar-shadow")) appBar?.classList.add("app-bar-shadow");
			} else {
				if (appBar?.classList.contains("app-bar-shadow")) appBar?.classList.remove("app-bar-shadow");
			}
		};

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
