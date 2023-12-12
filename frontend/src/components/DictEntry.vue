<template lang="pug">
.entry(ref="entry")
    v-container.words
        v-container.wordFrom(v-for="SourceString in dictEntry.source_strings", :class="SourceString.active")
            .wordActions
                v-btn.wordAction.disable(flat, size="x-small", icon="mdi-eye-off-outline")
                v-btn.wordAction.delete(flat, size="x-small", icon="mdi-trash-can-outline")
            .word(contenteditable="true") {{ SourceString.string }}
            .moveWordContainer
                v-btn.moveWord.up(flat, size="small" icon="mdi-menu-up")
                v-btn.moveWord.down(flat, size="small" icon="mdi-menu-down")
        v-btn.newEntry(flat, icon="mdi-plus-circle-outline")
    .divider
        .arrow
            img(src="@/assets/dict-arrow.svg")
    v-container.words
        v-container.wordTo
            .word(contenteditable="true") {{ dictEntry.to }}
    .moveEntries
        v-btn.moveEntry.up(flat, icon="mdi-menu-up", @click="moveEntryUp")
        v-btn.moveEntry.down(flat, icon="mdi-menu-down", @click="moveEntryDown")
    v-card-actions.dictActions
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
import { DictEntry } from "@/utils/dict";
import type { PropType } from "vue";

export default {
	name: "dict-entry",
	props: {
		dictEntry: {
			type: Object as PropType<DictEntry>,
			required: true,
		},
	},
	data() {
		return {
			originalDictEntry: this.dictEntry,
		};
	},
	methods: {
		addToggleActiveListeners() {
			var component = this;
            // @ts-ignore
			var btns = component.$refs.entry.getElementsByClassName("wordAction disable");
			for (var i = 0; i < btns.length; i++) {
				btns[i].addEventListener("click", function () {
					component.dictEntry.source_strings[i].active = !component.dictEntry.source_strings[i].active;
					component.dictEntry.locked = component.checkForChanges();
				});
			}
		},
		addDeleteWordListeners() {
			var component = this;
            // @ts-ignore
			var btns = this.$refs.entry.getElementsByClassName("wordAction delete");
			for (var i = 0; i < btns.length; i++) {
				btns[i].addEventListener("click", function () {
					component.dictEntry.source_strings.splice(i, 1);
					component.dictEntry.locked = component.checkForChanges();
				});
			}
		},
		addMoveWordUpListeners() {
			var component = this;
            // @ts-ignore
			var btns = this.$refs.entry.getElementsByClassName("moveWord up");
			for (var i = 0; i < btns.length; i++) {
				btns[i].addEventListener("click", function () {
					var temp = component.dictEntry.source_strings[i - 1];
					component.dictEntry.source_strings[i - 1] = component.dictEntry.source_strings[i];
					component.dictEntry.source_strings[i] = temp;
                    component.dictEntry.locked = component.checkForChanges();
				});
			}
		},
		addMoveWordDownListeners() {
			var component = this;
            // @ts-ignore
			var btns = this.$refs.entry.getElementsByClassName("moveWord down");
			for (var i = 0; i < btns.length; i++) {
				btns[i].addEventListener("click", function () {
                    if (i < component.dictEntry.source_strings.length - 1) {
                        var temp = component.dictEntry.source_strings[i + 1];
						component.dictEntry.source_strings[i + 1] = component.dictEntry.source_strings[i];
						component.dictEntry.source_strings[i] = temp;
					}
                    component.dictEntry.locked = component.checkForChanges();
				});
			}
		},
		addEditWordListeners() {
			var component = this;
            // @ts-ignore
			var words = this.$refs.entry.getElementsByClassName("word");
			for (var i = 0; i < words.length; i++) {
				words[i].addEventListener("input", function () {
					component.dictEntry.source_strings[i].string = words[i].innerHTML;
					component.dictEntry.locked = component.checkForChanges();
				});
			}
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
			this.dictEntry.locked = true;
		},
		moveEntryDown() {
			this.$emit("moveEntryDown", this.originalDictEntry);
			this.dictEntry.locked = true;
		},
		deleteEntry() {
			this.$emit("deleteEntry", this.originalDictEntry);
			this.dictEntry.locked = true;
		},
		submitChanges() {
			this.dictEntry.locked = false;
		},
		discardChanges() {
			this.dictEntry.source_strings = this.originalDictEntry.source_strings;
			this.dictEntry.to = this.originalDictEntry.to;
			this.dictEntry.active = this.originalDictEntry.active;
			this.dictEntry.locked = false;
		},
	},
	mounted() {
		this.addToggleActiveListeners();
		this.addDeleteWordListeners();
		this.addMoveWordUpListeners();
		this.addMoveWordDownListeners();
		this.addEditWordListeners();
	},
};
</script>
