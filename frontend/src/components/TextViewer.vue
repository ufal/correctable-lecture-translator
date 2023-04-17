<template lang="pug">
.translation(:style="styleFontSize", v-html="getFinalText")
</template>

<script lang="ts">
import { TextChunk } from "@/utils/chunk";
import type { PropType } from "vue";
import "@/styles/editChunk.scss";
import AsrClient from "@/utils/client";

export default {
	name: "text-viewer",
	props: {
		fontSize: {
			type: Number,
			required: true,
		},
		client: {
			type: Object as PropType<AsrClient>,
			required: true,
		},
		textChunks: {
			type: Array as PropType<TextChunk[]>,
			required: true,
		},
	},

	data() {
		return {
			styleFontSize: "font-size: " + this.fontSize.toString() + "px",
		};
	},

	computed: {
		getFinalText() {
			const colorGradient = ["#909090", "#c1c1c1"];
			let finalText = this.textChunks
				.slice(0, -colorGradient.length)
				.map(({ text }) => text)
				.join(" ");

			for (let i = 0; i < colorGradient.length; i++) {
				finalText += "<span style='color: " + colorGradient[i] + "'>";
				this.textChunks.at(-2 + i) == null
					? (finalText += "")
					: (finalText +=
							" " +
							this.textChunks.at(-colorGradient.length + i)
								?.text);
				finalText += "</span>";
			}
			return finalText;
		},
	},
};
</script>
