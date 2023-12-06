<template lang="pug">
v-container.dict
	span.subTitle Global dictionary
	.record
		v-container.words
			v-container.wordFrom
				.dictActions
					v-btn.dictAction.disable(flat, size="x-small", icon="mdi-eye-off-outline")
					v-btn.dictAction.delete(flat, size="x-small" icon="mdi-delete-forever-outline")
				span TEST
			v-container.wordFrom
				.dictActions
					v-btn.dictAction.disable(flat, size="x-small", icon="mdi-eye-off-outline")
					v-btn.dictAction.delete(flat, size="x-small" icon="mdi-delete-forever-outline")
				span TEST
			v-container.wordFrom
				.dictActions
					v-btn.dictAction.disable(flat, size="x-small", icon="mdi-eye-off-outline")
					v-btn.dictAction.delete(flat, size="x-small" icon="mdi-delete-forever-outline")
				span TEST
			v-btn.newEntry(flat, icon="mdi-plus-circle-outline")
		v-divider.arrow(thickness="2", length="200")
		v-container.words
			v-container.wordTo
				span TEST
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
		var btns = document.getElementsByClassName("dictAction disable");
		for (var i = 0; i < btns.length; i++) {
			btns[i].addEventListener("click", function () {
				// @ts-ignore
				var dictActions = this.parentElement;
				var word = dictActions.parentElement;
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
