<template lang="pug">

v-app-bar#appBar(:elevation="0")
	template(v-slot:prepend)
		v-icon.logo(
			icon="mdi-translate",
		)
		.title Coletra
		v-divider.logoSpacer(vertical, inset, thickness="2", length="40")
		#menuBtnsContainer
			.v-btn(@click="editorMode = false").menuBtn.active Viewer
			.v-btn(@click="editorMode = true").menuBtn Editor
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
	v-divider(:thickness="3").bigDivider
	text-editor(:client="client", :textChunks="textChunks")

v-container.viewer(v-else)
	#viewingModeBtnsContainer
		v-btn.viewingModeBtn.active(icon="mdi-file-eye-outline" size="large" @click="viewingMode = 'normal'")
		v-btn.viewingModeBtn(icon="mdi-projector" size="large" @click="viewingMode = 'presentation'")
	text-viewer.viewing-viewer(:client="client", :textChunks="textChunks")

</template>

<script lang="ts">
import "@/styles/viewing.scss";
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
			updateInterval: 1000,
			updateIntervalId: 0,
			toggleUpdatesIcon: "mdi-play",
			editorMode: true,
			toggleUpdatesColor: "#5b3e87",
			viewingMode: "normal",
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

				this.updateIntervalId = window.setInterval(this.updateText, this.updateInterval);
				this.toggleUpdatesIcon = "mdi-pause";
				this.toggleUpdatesColor = "#ea9d34";
				console.info("Started updating text.");
			} else {
				window.clearInterval(this.updateIntervalId);
				this.updateIntervalId = 0;
				this.toggleUpdatesIcon = "mdi-play";
				this.toggleUpdatesColor = "#5b3e87";
				console.info("Stopped updating text.");
			}
		},
		uglyHack() {
			var fontSizes = ["1rem", "2.5rem"];
			var translation = document.getElementsByClassName("translation")[0];
			if (translation == undefined) return;
			var viewingModeBtnsContainer = document.getElementById("viewingModeBtnsContainer");
			var viewingModeBtns = viewingModeBtnsContainer!.getElementsByClassName("viewingModeBtn");
			for (var i = 0; i < viewingModeBtns.length; i++) {
				viewingModeBtns[i].addEventListener("click", function () {
					var current = viewingModeBtnsContainer!.getElementsByClassName("active");
					if (current.length > 0) {
						current[0].className = current[0].className.replace(" active", "");
					}
					// @ts-ignore
					this.className += " active";
					// @ts-ignore
					translation.style.fontSize = fontSizes[Array.from(viewingModeBtns).indexOf(this)];
				});
			}
		},
	},
	async mounted() {
		// this.textChunks = await this.client.getLatestTextChunks({});
		var menuBtnsContainer = document.getElementById("menuBtnsContainer");
		var menuBtns = menuBtnsContainer!.getElementsByClassName("menuBtn");
		for (var i = 0; i < menuBtns.length; i++) {
			var that = this;
			menuBtns[i].addEventListener("click", function () {
				var current = menuBtnsContainer!.getElementsByClassName("active");
				if (current.length > 0) {
					current[0].className = current[0].className.replace(" active", "");
				}
				// @ts-ignore
				this.className += " active";
				that.uglyHack();
			});
		}

		this.uglyHack();

		document.onscroll = () => {
			let appBar = document.getElementById("appBar");
			if (window.scrollY > 10) {
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
