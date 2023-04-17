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
		color="#188B61",
		@click="submitTextChunk"
	) Submit
	v-btn.discardChanges(
		v-if="showSubmit",
		size="small",
		color="#bd3f4f",
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
			highlightSpan:
				"<span style='background-color: #E0D64E; color: black'>",
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

			if (this.updatedText != this.originalText) this.showSubmit = true;
			else this.showSubmit = false;
		},
		highlightFocused(e: any) {
			this.chunk.text = this.highlightSpan + this.chunk.text + "</span>";
		},
		unhighlightFocused(e: any) {
			this.chunk.text = this.chunk.text
				.replace(this.highlightSpan, "")
				.replace("</span>", "");
		},
		discardChanges() {
			this.updatedText = this.originalText;
			// Ugly hack to update displayed variable
			// the space is discarded during html render
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
