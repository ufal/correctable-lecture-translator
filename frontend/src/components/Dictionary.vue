<template lang="pug">
v-container.dict
    .test
    img.line(src="@/assets/dict-line.png")
    //- img(src="@/assets/dict-line-pine.png")
</template>

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
};
</script>
