<template lang="pug">
v-card.container
	.editTextChunk(
		contenteditable="true",
		@input="onInput",
		@focus="highlightFocused",
		@blur="unhighlightFocused",
		v-html="originalText"
	)
	v-btn.submitChanges(
		v-if="showSubmit",
		size="small",
		@click="submitTextChunk"
	) Submit
	v-btn.discardChanges(
		v-if="showSubmit",
		size="small",
		@click="discardChanges"
	) Discard
</template>

<script lang="ts">
import { TextChunk } from "@/utils/chunk";
import type { PropType } from "vue";
import "@/styles/editChunk.scss";
import AsrClient from "@/utils/client";

export default {
	name: "edit-text-chunk",
	props: {
		client: {
			type: Object as PropType<AsrClient>,
			required: true,
		},
		chunk: {
			type: Object as PropType<TextChunk>,
			required: true,
		},
	},
	data() {
		return {
			originalText: "" as string,
			updatedText: "" as string,
			showSubmit: false,
			highlightSpan: "<span style='background-color: #cfdedd; color: black'>",
		};
	},
	methods: {
		submitTextChunk() {
			if (this.updatedText !== this.originalText) {
				this.client.updateTextChunk({
					timestamp: this.chunk.timestamp,
					version: this.chunk.version,
					text: this.updatedText,
				} as TextChunk);
				this.showSubmit = false;
			}
		},
		onInput(e: any) {
			this.updatedText = e.target.innerHTML;
			if (this.updatedText.trim() != this.originalText.trim()) {
				this.showSubmit = true;
				console.log("submit");
			} else {
				console.log("discard");
				this.showSubmit = false;
			}
		},
		highlightFocused(e: any) {
			this.chunk.text = this.highlightSpan + this.chunk.text + "</span>";
		},
		unhighlightFocused(e: any) {
			this.chunk.text = this.chunk.text.replace(this.highlightSpan, "").replace("</span>", "");
		},
		discardChanges() {
			this.updatedText = this.originalText;
			// Ugly hack to update displayed variable.
			// The "space" is discarded during the render.
			this.originalText = this.originalText + " ";
			this.showSubmit = false;
		},
	},

	mounted() {
		this.originalText = this.chunk.text;
		this.updatedText = this.originalText;
	},
};
</script>
