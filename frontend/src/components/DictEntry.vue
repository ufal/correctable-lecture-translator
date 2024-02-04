<template lang="pug">
.entry(ref="entry")
    v-container.words
        v-container.wordFrom(v-for="(SourceString, SourceStringIndex) in dictEntry.source_strings", :class="SourceString.active")
            .wordActions
                v-btn.wordAction.disable(flat, size="x-small", icon="mdi-eye-off-outline", @click="toggleWord($event, SourceStringIndex)")
                v-btn.wordAction.delete(flat, size="x-small", icon="mdi-trash-can-outline", @click="deleteWord(SourceStringIndex)")
            .word(contenteditable="true" @input="editWordFrom($event, SourceStringIndex)") {{ SourceString.string }}
            .moveWordContainer(:class="{ invisible: !(dictEntry.source_strings.length > 1) }")
                v-btn.moveWord.up(flat, size="x-small", icon="mdi-menu-up", @click="moveWordUp(SourceStringIndex)")
                v-btn.moveWord.down(flat, size="x-small" icon="mdi-menu-down" @click="moveWordDown(SourceStringIndex)")
        v-btn.newEntry(flat, size="x-small", icon="mdi-plus-circle-outline" @click="addWord")
    .divider
        .arrow
            img(src="@/assets/dict-arrow.svg")
    v-container.words
        v-container.wordTo
            .word(contenteditable="true" @input="editWordTo") {{ dictEntry.to }}
    .moveEntryContainer
        v-btn.moveEntry(flat, icon="mdi-menu-up", @click="moveEntryUp")
        v-btn.deleteEntry(flat, size="x-small", icon="mdi-trash-can-outline", @click="deleteEntry")
        v-btn.moveEntry(flat, icon="mdi-menu-down", @click="moveEntryDown")
    .dictEntryActions(v-if="dictEntry.locked")
        v-btn.discardChanges(
            size="small",
            @click="discardChanges"
        ) Discard
</template>

<script lang="ts">
import "@/styles/dictionary.scss";
import { DictEntryType, DictType } from "@/utils/dict";
import type { PropType } from "vue";

export default {
	name: "dict-entry",
	props: {
		dictEntry: {
			type: Object as PropType<DictEntryType>,
			required: true,
		},
		dictEntryIndex: {
			type: Number,
			required: true,
		},
		originalDict: {
			type: Object as PropType<DictType[]>,
			required: true,
		},
	},
	computed: {
		originalDictEntry() {
			// @ts-ignore
			return this.originalDict.entries.find((dictEntry) => dictEntry.to == this.dictEntry.to);
		},
	},
	methods: {
		checkForChanges() {
			if (this.originalDictEntry == undefined) {
				return true;
			}
			if (this.dictEntry.to != this.originalDictEntry.to) {
				return true;
			}
			if (this.dictEntry.source_strings.length != this.originalDictEntry.source_strings.length) {
				return true;
			}
			for (var i = 0; i < this.dictEntry.source_strings.length; i++) {
				if (this.dictEntry.source_strings[i].string != this.originalDictEntry.source_strings[i].string) {
					return true;
				}
				if (this.dictEntry.source_strings[i].active != this.originalDictEntry.source_strings[i].active) {
					return true;
				}
			}
			return false;
		},
		moveWordUp(index: number) {
			if (index - 1 < 0) {
				// index is 0, add element to the end and remove it from start
				this.dictEntry.source_strings.push(this.dictEntry.source_strings[0]);
				this.dictEntry.source_strings.splice(0, 1);
			} else {
				var temp = this.dictEntry.source_strings[index - 1];
				this.dictEntry.source_strings[index - 1] = this.dictEntry.source_strings[index];
				this.dictEntry.source_strings[index] = temp;
			}
		},
		moveWordDown(index: number) {
			if (index + 1 > this.dictEntry.source_strings.length - 1) {
				// index is last, add element to the start and remove it from end
				this.dictEntry.source_strings.unshift(
					this.dictEntry.source_strings[this.dictEntry.source_strings.length - 1],
				);
				this.dictEntry.source_strings.splice(this.dictEntry.source_strings.length - 1, 1);
			} else {
				var temp = this.dictEntry.source_strings[index + 1];
				this.dictEntry.source_strings[index + 1] = this.dictEntry.source_strings[index];
				this.dictEntry.source_strings[index] = temp!;
			}
		},
		editWordFrom(e: Event, index: number) {
			// @ts-ignore
			this.dictEntry.source_strings[index].string = e.target.innerHTML;
		},
		editWordTo(e: Event) {
			// @ts-ignore
			this.dictEntry.to = e.target.innerHTML;
		},
		toggleWord(e: Event, index: number) {
			this.dictEntry.source_strings[index].active = !this.dictEntry.source_strings[index].active;
			// @ts-ignore
			e.target.classList.toggle("active");
		},
		deleteWord(index: number) {
			this.dictEntry.source_strings.splice(index, 1);
		},
		addWord() {
			this.dictEntry.source_strings.push({
				string: "TEXT_TO_REPLACE",
				active: true,
			});
		},
		moveEntryUp() {
			this.$emit("moveEntryUp", this.dictEntry.to);
		},
		deleteEntry() {
			this.$emit("deleteEntry", this.dictEntry.to);
		},
		moveEntryDown() {
			this.$emit("moveEntryDown", this.dictEntry.to);
		},
		discardChanges() {
			if (this.originalDictEntry == undefined) {
				this.$emit("deleteEntry", this.dictEntry.to);
				return;
			}
			// deep copy source_strings
			this.dictEntry.source_strings = JSON.parse(JSON.stringify(this.originalDictEntry.source_strings));
			this.dictEntry.to = this.originalDictEntry.to;
			this.dictEntry.active = this.originalDictEntry.active;
		},
	},
	watch: {
		$props: {
			handler: function () {
				this.dictEntry.locked = this.checkForChanges();
			},
			deep: true,
		},
	},
};
</script>
