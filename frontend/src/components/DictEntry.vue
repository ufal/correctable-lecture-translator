<template lang="pug">
.entry(ref="entry")
    v-container.words
        v-container.wordFrom(v-for="(SourceString, SourceStringIndex) in dictEntry.source_strings", :class="SourceString.active")
            .wordActions
                v-btn.wordAction.disable(flat, size="x-small", icon="mdi-eye-off-outline", @click="toggleWord($event, SourceStringIndex)")
                v-btn.wordAction.delete(flat, size="x-small", icon="mdi-trash-can-outline", @click="deleteWord(SourceStringIndex)")
            .word(contenteditable="true" @input="editWordFrom($event, SourceStringIndex)") {{ SourceString.string }}
            .moveWordContainer
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
        v-btn.moveEntry.up(flat, icon="mdi-menu-up", @click="moveEntryUp")
        v-btn.moveEntry.down(flat, icon="mdi-menu-down", @click="moveEntryDown")
    .dictActions(v-if="dictEntry.locked")
        v-btn.submitChanges(
            size="small",
            @click="submitChanges"
        ) Submit
        v-btn.discardChanges(
            size="small",
            @click="discardChanges"
        ) Discard
    </template>

<script lang="ts">
import "@/styles/dictionary.scss";
import { DictEntryType } from "@/utils/dict";
import type { PropType } from "vue";

export default {
	name: "dict-entry",
	props: {
		dictEntry: {
			type: Object as PropType<DictEntryType>,
			required: true,
		},
	},
	data() {
		return {
			// copy object value
			originalDictEntry: JSON.parse(JSON.stringify(this.dictEntry)),
		};
	},
	methods: {
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
			this.dictEntry.locked = this.checkForChanges();
		},
		moveWordDown(index: number) {
			if (index + 1 > this.dictEntry.source_strings.length - 1) {
				// index is last, add element to the start and remove it from end
				this.dictEntry.source_strings.unshift(
					this.dictEntry.source_strings[this.dictEntry.source_strings.length - 1],
				);
				this.dictEntry.source_strings.splice(this.dictEntry.source_strings.length - 1, 1);
			} else {
				var temp = this.dictEntry.source_strings.at(index + 1);
				this.dictEntry.source_strings[index + 1] = this.dictEntry.source_strings.at(index)!;
				this.dictEntry.source_strings[index] = temp!;
			}
			this.dictEntry.locked = this.checkForChanges();
		},
		editWordFrom(e: Event, index: number) {
			// @ts-ignore
			this.dictEntry.source_strings[index].string = e.target.innerHTML;
			this.dictEntry.locked = this.checkForChanges();
		},
		editWordTo(e: Event) {
			// @ts-ignore
			this.dictEntry.to = e.target.innerHTML;
			this.dictEntry.locked = this.checkForChanges();
		},
		toggleWord(e: Event, index: number) {
			this.dictEntry.source_strings[index].active = !this.dictEntry.source_strings[index].active;
            // @ts-ignore
            e.target.classList.toggle("active");
			this.dictEntry.locked = this.checkForChanges();
		},
		deleteWord(index: number) {
			this.dictEntry.source_strings.splice(index, 1);
			this.dictEntry.locked = this.checkForChanges();
		},
		addWord() {
			this.dictEntry.source_strings.push({
				string: "TEXT_TO_REPLACE",
				active: true,
			});
			this.dictEntry.locked = this.checkForChanges();
		},
		checkForChanges() {
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
		moveEntryUp() {
			this.$emit("moveEntryUp", this.originalDictEntry);
		},
		moveEntryDown() {
			this.$emit("moveEntryDown", this.originalDictEntry);
		},
		deleteEntry() {
			this.$emit("deleteEntry", this.originalDictEntry);
			this.dictEntry.locked = true;
		},
		submitChanges() {
			this.$emit("submitChanges", this.dictEntry);
			this.dictEntry.locked = false;
		},
		discardChanges() {
			this.dictEntry.source_strings = this.originalDictEntry.source_strings;
			this.dictEntry.to = this.originalDictEntry.to;
			this.dictEntry.active = this.originalDictEntry.active;
			this.dictEntry.locked = false;
		},
	},
	mounted() {},
};
</script>
