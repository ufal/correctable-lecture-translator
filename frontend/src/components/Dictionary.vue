<template lang="pug">
v-container.dict
	span.subTitle Global Phrase Replacement Rules
	dict-entry(v-for="DictEntry in localDict.entries" , :dictEntry="DictEntry", :originalDict="localDictOriginal" @move-entry-up="moveEntryUp", @move-entry-down="moveEntryDown")
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
			localDict: {
				entries: [
					{
						to: "TEST_TO_1",
						source_strings: [
							{
								string: "TEST_FROM_1",
								active: true,
							},
							{
								string: "TEST_FROM_2",
								active: true,
							},
							{
								string: "TEST_FROM_3",
								active: true,
							},
						],
						active: true,
						locked: false,
					} as DictEntryType,
					{
						to: "TEST_TO_2",
						source_strings: [
							{
								string: "TEST_FROM_1",
								active: true,
							},
							{
								string: "TEST_FROM_2",
								active: true,
							},
						],
						active: true,
						locked: false,
					} as DictEntryType,
					{
						to: "TEST_TO_3",
						source_strings: [
							{
								string: "TEST_FROM_1",
								active: true,
							},
						],
						active: true,
						locked: false,
					} as DictEntryType,
				],
				locked: false,
			} as DictType,
			serverDict: {} as DictType,
			localDictOriginal: {} as DictType,
		};
	},
	methods: {
		checkForChanges() {
			if (this.localDict.entries.length != this.localDictOriginal.entries.length) {
				return true;
			}
			for (var i = 0; i < this.localDict.entries.length; i++) {
				if (this.localDict.entries[i].locked) {
					return true;
				}
				if (this.localDict.entries[i].to != this.localDictOriginal.entries[i].to) {
					return true;
				}
			}
			return false;
		},
		moveEntryUp(to: string) {
			var index = this.localDict.entries.findIndex((dictEntry) => dictEntry.to == to);

			if (index - 1 < 0) {
				// index is 0, add element to the end and remove it from start
				this.localDict.entries.push(this.localDict.entries[0]);
				this.localDict.entries.splice(0, 1);
			} else {
				var temp = this.localDict.entries[index - 1];
				this.localDict.entries[index - 1] = this.localDict.entries[index];
				this.localDict.entries[index] = temp;
			}
			this.localDict.locked = this.checkForChanges();
			console.log(this.localDict.locked);
		},
		moveEntryDown(to: string) {
			var index = this.localDict.entries.findIndex((dictEntry) => dictEntry.to == to);
			console.log(index);
			if (index + 1 > this.localDict.entries.length - 1) {
				// index is last, add element to the start and remove it from end
				this.localDict.entries.unshift(this.localDict.entries[this.localDict.entries.length - 1]);
				this.localDict.entries.splice(this.localDict.entries.length - 1, 1);
			} else {
				var temp = this.localDict.entries[index + 1];
				this.localDict.entries[index + 1] = this.localDict.entries[index];
				this.localDict.entries[index] = temp!;
			}
			this.localDict.locked = this.checkForChanges();
			console.log(this.localDict.locked);
		},
	},
	async mounted() {
		// this.localDict = await this.client.getDict();
		// this.serverDict = await this.client.getDict();
		this.localDictOriginal = JSON.parse(JSON.stringify(this.localDict));
		this.serverDict = JSON.parse(JSON.stringify(this.localDict));

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
