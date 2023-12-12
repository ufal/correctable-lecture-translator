<template lang="pug">
v-container.dict
	span.subTitle Global Phrase Replacement Rules
	dict-entry(:dictEntry="dictEntry")
	v-btn.newEntry(flat, icon="mdi-plus-circle-outline")

</template>

<script lang="ts">
import type { PropType } from "vue";
import "@/styles/dictionary.scss";
import AsrClient from "@/utils/client";
import DictEntry from "@/components/DictEntry.vue";
import { DictType, DictEntryType } from "@/utils/dict";

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
			localDict: [] as DictEntryType[],
			serverDict: [] as DictEntryType[],
			dictEntry: {
				to: "TEST_TO",
				source_strings: [
					{
						string: "TEST_FROM_1",
						active: true,
					},
					{
						string: "TEST_FROM_2",
						active: true,
					},{
						string: "TEST_FROM_3",
						active: true,
					},
				],
				active: true,
				locked: false,
			} as DictEntryType,
		};
	},
	async mounted() {
		// this.localDict = await this.client.getDict();
		// this.serverDict = await this.client.getDict();

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
