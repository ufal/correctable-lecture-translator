<template lang="pug">
v-container
	edit-text-chunk(
		v-for="chunk in textChunks",
		:client="client",
		:chunk="chunk"
	)
</template>

<script lang="ts">
import { TextChunk } from "@/utils/chunk";
import AsrClient from "@/utils/client";
import { PropType } from "vue";

export default {
	name: "text-editor",
	props: {
		client: {
			type: Object as PropType<AsrClient>,
			required: true,
		},
		textChunks: {
			type: Array as PropType<TextChunk[]>,
			required: true,
		},
	},
};
</script>
