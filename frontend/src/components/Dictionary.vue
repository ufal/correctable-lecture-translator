<template lang="pug">
v-container.dict
	span.subTitle Global Phrase Replacement Rules
	.record
		v-container.words
			v-container.wordFrom
				.wordActions
					v-btn.wordAction.disable(flat, size="x-small", icon="mdi-eye-off-outline")
					v-btn.wordAction.delete(flat, size="x-small" icon="mdi-trash-can-outline")
				.word(contenteditable="true") {{ originalText }}
				.moveWordContainer
					v-btn.moveWord(flat, size="small" icon="mdi-menu-up")
					v-btn.moveWord(flat, size="small" icon="mdi-menu-down")
			v-container.wordFrom
				.wordActions
					v-btn.wordAction.disable(flat, size="x-small", icon="mdi-eye-off-outline")
					v-btn.wordAction.delete(flat, size="x-small" icon="mdi-trash-can-outline")
				.word(contenteditable="true") Replace this many words with a single beautiful fancy word
				.moveWordContainer
					v-btn.moveWord(flat, size="small" icon="mdi-menu-up")
					v-btn.moveWord(flat, size="small" icon="mdi-menu-down")
			v-container.wordFrom
				.wordActions
					v-btn.wordAction.disable(flat, size="x-small", icon="mdi-eye-off-outline")
					v-btn.wordAction.delete(flat, size="x-small" icon="mdi-trash-can-outline")
				.word(contenteditable="true") this words man
				.moveWordContainer
					v-btn.moveWord(flat, size="small" icon="mdi-menu-up")
					v-btn.moveWord(flat, size="small" icon="mdi-menu-down")
			v-btn.newEntry(flat, icon="mdi-plus-circle-outline")

		.divider
			.arrow
				img(src="@/assets/dict-arrow.svg")
		v-container.words
			v-container.wordTo
				.word(contenteditable="true") RoBERTa
		.moveEntries
			v-btn.moveEntry(flat, icon="mdi-menu-up")
			v-btn.moveEntry(flat, icon="mdi-menu-down")
		v-card-actions.dictActions
			v-btn.submitChanges(
				size="small",
			) Submit
			v-btn.discardChanges(
				size="small",
			) Discard
	.record
		v-container.words
			v-container.wordFrom
				.wordActions
					v-btn.wordAction.disable(flat, size="x-small", icon="mdi-eye-off-outline")
					v-btn.wordAction.delete(flat, size="x-small" icon="mdi-trash-can-outline")
				.word(contenteditable="true") {{ originalText }}
				.moveWordContainer
					v-btn.moveWord(flat, size="small" icon="mdi-menu-up")
					v-btn.moveWord(flat, size="small" icon="mdi-menu-down")
			v-container.wordFrom
				.wordActions
					v-btn.wordAction.disable(flat, size="x-small", icon="mdi-eye-off-outline")
					v-btn.wordAction.delete(flat, size="x-small" icon="mdi-trash-can-outline")
				.word(contenteditable="true") Replace this many words with a single beautiful fancy word
				.moveWordContainer
					v-btn.moveWord(flat, size="small" icon="mdi-menu-up")
					v-btn.moveWord(flat, size="small" icon="mdi-menu-down")
			v-container.wordFrom
				.wordActions
					v-btn.wordAction.disable(flat, size="x-small", icon="mdi-eye-off-outline")
					v-btn.wordAction.delete(flat, size="x-small" icon="mdi-trash-can-outline")
				.word(contenteditable="true") this words man
				.moveWordContainer
					v-btn.moveWord(flat, size="small" icon="mdi-menu-up")
					v-btn.moveWord(flat, size="small" icon="mdi-menu-down")
			v-btn.newEntry(flat, icon="mdi-plus-circle-outline")
		.divider
			.arrow
				img(src="@/assets/dict-arrow.svg")
		v-container.words
			v-container.wordTo
				.word(contenteditable="true") Mrkvicka
		.moveEntries
			v-btn.moveEntry(flat, icon="mdi-menu-up")
			v-btn.moveEntry(flat, icon="mdi-menu-down")
		v-card-actions.dictActions
			v-btn.submitChanges(
				size="small",
			) Submit
			v-btn.discardChanges(
				size="small",
			) Discard
	v-btn.newEntry(flat, icon="mdi-plus-circle-outline")

</template>
<!-- img.line(src="@/assets/dict-line.png") -->

<script lang="ts">
import type { PropType } from "vue";
import "@/styles/dictionary.scss";
import AsrClient from "@/utils/client";

export default {
	name: "global-dictionary",
	props: {
		client: {
			type: Object as PropType<AsrClient>,
			required: true,
		},
	},
	data() {
		return {
			originalText: "Robert" as string,
		};
	},

	async mounted() {
		// TODO: refactor to a separate function and reuse
		var btns = document.getElementsByClassName("wordAction disable");
		for (var i = 0; i < btns.length; i++) {
			btns[i].addEventListener("click", function () {
				// @ts-ignore
				var wordActions = this.parentElement;
				var word = wordActions.parentElement;
				if (word.classList.contains("disable")) {
					word.classList.remove("disable");
				} else {
					word.classList.add("disable");
				}
			});
		}
	},
};
</script>
