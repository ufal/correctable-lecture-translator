<template lang="pug">
.container
	.textFeedback
		.editTextChunk(
			contenteditable="true",
			@input="onInput",
			@focus="highlightFocused",
			@blur="unhighlightFocused",
			v-html="originalText"
		)
		.feedback
			v-btn.like(
				size="small",
				:icon="likeIcon",
				@click="likeTextChunk"
			)
			v-btn.dislike(
				size="small",
				:icon="dislikeIcon",
				@click="dislikeTextChunk"
			)
	.actions(v-if="showSubmit")
		v-btn.submitChanges(
			size="small",
			@click="submitTextChunk"
		) Submit
		v-btn.discardChanges(
			size="small",
			@click="discardChanges"
		) Discard
</template>

<script lang="ts">
import { TextChunk } from "@/utils/chunk";
import type { PropType } from "vue";
import "@/styles/editTextChunk.scss";
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
			likeIcon: "mdi-thumb-up-outline",
			dislikeIcon: "mdi-thumb-down-outline",
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
			} else {
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
		likeTextChunk() {
			var rating = 0;
			if (this.likeIcon == "mdi-thumb-up-outline") {
				this.likeIcon = "mdi-thumb-up";
				if (this.dislikeIcon == "mdi-thumb-down") {
					this.dislikeIcon = "mdi-thumb-down-outline";
					rating++;
				}
				rating++;
			} else {
				this.likeIcon = "mdi-thumb-up-outline";
				rating--;
			}
			this.client.rateTextChunk(this.chunk, rating);
		},
		dislikeTextChunk() {
			var rating = 0;
			if (this.dislikeIcon == "mdi-thumb-down-outline") {
				this.dislikeIcon = "mdi-thumb-down";
				if (this.likeIcon == "mdi-thumb-up") {
					this.likeIcon = "mdi-thumb-up-outline";
					rating--;
				}
				rating--;
			} else {
				this.dislikeIcon = "mdi-thumb-down-outline";
				rating++;
			}
			this.client.rateTextChunk(this.chunk, rating);
		},
	},

	mounted() {
		this.originalText = this.chunk.text;
		this.updatedText = this.originalText;
	},
};
</script>
