<template lang="pug">
v-container.dict
	span.subTitle Global dictionary
	.record
		v-container.words
			v-container.wordFrom
				.wordActions
					v-btn.wordAction.disable(flat, size="x-small", icon="mdi-eye-off-outline")
					v-btn.wordAction.delete(flat, size="x-small" icon="mdi-delete-forever-outline")
				span Robert
			v-container.wordFrom
				.wordActions
					v-btn.wordAction.disable(flat, size="x-small", icon="mdi-eye-off-outline")
					v-btn.wordAction.delete(flat, size="x-small" icon="mdi-delete-forever-outline")
				span Replace this many words with a single beautiful fancy word
			v-container.wordFrom
				.wordActions
					v-btn.wordAction.disable(flat, size="x-small", icon="mdi-eye-off-outline")
					v-btn.wordAction.delete(flat, size="x-small" icon="mdi-delete-forever-outline")
				span this words man
			v-btn.newEntry(flat, icon="mdi-plus-circle-outline")
		v-divider.arrow(thickness="2", length="200")
		v-container.words
			v-container.wordTo
				span RoBERTa
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
