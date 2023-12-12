<template lang="pug">
v-container.dict
	span.subTitle Global Phrase Replacement Rules

	v-btn.newEntry(flat, icon="mdi-plus-circle-outline")

</template>

<script lang="ts">
import type { PropType } from "vue";
import "@/styles/dictionary.scss";
import AsrClient from "@/utils/client";
import { Dict } from "@/utils/dict";

export default {
	name: "dictionary",
	props: {
		client: {
			type: Object as PropType<AsrClient>,
			required: true,
		},
	},
	data() {
		return {
			localDict: [] as Dict[],
			serverDict: [] as Dict[],
		};
	},
	async mounted() {
		this.localDict = await this.client.getDict();
		this.serverDict = await this.client.getDict();

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
