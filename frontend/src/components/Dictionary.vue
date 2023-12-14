<template lang="pug">
v-container.dict
	span.subTitle Global Phrase Replacement Rules
	dict-entry(
		v-for="(DictEntry, DictEntryIndex) in localDict.entries",
		:dictEntry="DictEntry",
		:dictEntryIndex="DictEntryIndex",
		:originalDict="localDictOriginal",
		@move-entry-up="moveEntryUp",
		@delete-entry="deleteEntry",
		@move-entry-down="moveEntryDown"
	)
	.dictEntryActions(v-if="localDict.locked")
		v-btn.submitChanges(
			size="small",
			@click="submitChanges"
		) Submit
		v-btn.discardChanges(
			size="small",
			@click="discardChanges"
		) Discard
	v-btn.newEntry(flat, icon="mdi-plus-circle-outline", @click="addEntry")
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
		startUpdating: {
			type: Boolean,
			required: true,
		},
		updateInterval: {
			type: Number,
			required: true,
		},
	},
	data() {
		return {
			// localDict: {
			// 	entries: [
			// 		{
			// 			to: "TEST_TO_1",
			// 			source_strings: [
			// 				{
			// 					string: "TEST_FROM_1",
			// 					active: true,
			// 				},
			// 				{
			// 					string: "TEST_FROM_2",
			// 					active: true,
			// 				},
			// 				{
			// 					string: "TEST_FROM_3",
			// 					active: true,
			// 				},
			// 			],
			// 			active: true,
			// 			locked: false,
			// 		} as DictEntryType,
			// 		{
			// 			to: "TEST_TO_2",
			// 			source_strings: [
			// 				{
			// 					string: "TEST_FROM_1",
			// 					active: true,
			// 				},
			// 				{
			// 					string: "TEST_FROM_2",
			// 					active: true,
			// 				},
			// 			],
			// 			active: true,
			// 			locked: false,
			// 		} as DictEntryType,
			// 		{
			// 			to: "TEST_TO_3",
			// 			source_strings: [
			// 				{
			// 					string: "TEST_FROM_1",
			// 					active: true,
			// 				},
			// 			],
			// 			active: true,
			// 			locked: false,
			// 		} as DictEntryType,
			// 	],
			// 	locked: false,
			// } as DictType,
			localDict: {
				entries: [
					{
						to: "REPLACE_WITH_0",
						source_strings: [
							{
								string: "TEXT_TO_REPLACE",
								active: true,
							},
						],
						active: true,
						locked: false,
					} as DictEntryType,
				] as DictEntryType[],
				locked: false,
			} as DictType,
			serverDict: {} as DictType,
			localDictOriginal: {} as DictType,
			updateIntervalId: 0,
		};
	},
	methods: {
		checkForChanges() {
			if (this.localDict.entries == undefined) return false;
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

				this.localDictOriginal.entries.push(this.localDictOriginal.entries[0]);
				this.localDictOriginal.entries.splice(0, 1);
			} else {
				var temp = this.localDict.entries[index - 1];
				this.localDict.entries[index - 1] = this.localDict.entries[index];
				this.localDict.entries[index] = temp;
			}
		},
		deleteEntry(to: string) {
			var index = this.localDict.entries.findIndex((dictEntry) => dictEntry.to == to);
			this.localDict.entries.splice(index, 1);
		},
		moveEntryDown(to: string) {
			var index = this.localDict.entries.findIndex((dictEntry) => dictEntry.to == to);
			if (index + 1 > this.localDict.entries.length - 1) {
				// index is last, add element to the start and remove it from end
				this.localDict.entries.unshift(this.localDict.entries[this.localDict.entries.length - 1]);
				this.localDict.entries.splice(this.localDict.entries.length - 1, 1);

				this.localDictOriginal.entries.unshift(
					this.localDictOriginal.entries[this.localDictOriginal.entries.length - 1],
				);
				this.localDictOriginal.entries.splice(this.localDictOriginal.entries.length - 1, 1);
			} else {
				var temp = this.localDict.entries[index + 1];
				this.localDict.entries[index + 1] = this.localDict.entries[index];
				this.localDict.entries[index] = temp!;
			}
		},
		addEntry() {
			this.localDict.entries.push({
				to: "REPLACE_WITH_" + this.localDict.entries.length,
				source_strings: [
					{
						string: "TEXT_TO_REPLACE",
						active: true,
					},
				],
				active: true,
				locked: false,
			} as DictEntryType);
		},
		async submitChanges() {
			await this.client.submitDict(this.localDict);
			// unlock all entries
			this.localDict.entries.forEach((dictEntry) => {
				dictEntry.locked = false;
			});
			this.localDictOriginal = JSON.parse(JSON.stringify(this.localDict));
		},
		discardChanges() {
			// deep copy source_strings
			this.localDict = JSON.parse(JSON.stringify(this.localDictOriginal));
		},
		async updateDict() {
			if (this.localDict.locked) {
				return;
			}
			this.localDict = await this.client.getDict();
			this.localDictOriginal = JSON.parse(JSON.stringify(this.localDict));
		},
	},
	watch: {
		$data: {
			handler: function () {
				this.localDict.locked = this.checkForChanges();
			},
			deep: true,
		},
		startUpdating: {
			handler: function () {
				if (this.startUpdating) {
					console.log("Starting updating dict.");
					this.updateIntervalId = window.setInterval(this.updateDict, this.updateInterval);
				} else {
					console.log("Stopping updating dict.");
					window.clearInterval(this.updateIntervalId);
					this.updateIntervalId = 0;
				}
			},
		},
	},
	async mounted() {
		this.localDictOriginal = JSON.parse(JSON.stringify(this.localDict));
		this.serverDict = JSON.parse(JSON.stringify(this.localDict));

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
