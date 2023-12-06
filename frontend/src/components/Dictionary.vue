<template lang="pug">
v-container.dict
	v-container.words
		v-container.wordFrom
			.actions
				v-btn.action.disable(flat, size="x-small", icon="mdi-eye-off-outline")
				v-btn.action.delete(flat, size="x-small" icon="mdi-delete-forever-outline")
			span TEST
		v-container.wordFrom
			.actions
				v-btn.action.disable(flat, size="x-small", icon="mdi-eye-off-outline")
				v-btn.action.delete(flat, size="x-small" icon="mdi-delete-forever-outline")
			span TEST
		v-container.wordFrom
			.actions
				v-btn.action.disable(flat, size="x-small", icon="mdi-eye-off-outline")
				v-btn.action.delete(flat, size="x-small" icon="mdi-delete-forever-outline")
			span TEST
	v-divider.arrow(thickness="2", length="200")
	v-container.words
		v-container.wordTo
			span TEST
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
		var btns = document.getElementsByClassName("action disable");
		for (var i = 0; i < btns.length; i++) {
			btns[i].addEventListener("click", function () {
				// @ts-ignore
				var actions = this.parentElement;
				var word = actions.parentElement;
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
