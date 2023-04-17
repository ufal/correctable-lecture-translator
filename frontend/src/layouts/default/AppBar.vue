<template lang="pug">
v-app-bar(color="primary", prominent)
	//- v-app-bar-nav-icon
	v-toolbar-title(style="color: darkyello") Hermes
	v-container(style="max-width: 1000px")
		v-row(align="center", justify="end")
			v-col
				v-select.test(
					label="Select input language",
					v-model="language",
					:items="languages",
					variant="solo",
					density="compact",
					:style="{ padding: '20px 5px 0 0', maxWidth: '230px' }"
				)
					template(v-slot:prepend)
						v-icon mdi-translate

			v-col
				v-spacer

			v-col
				v-btn.testbtn(variant="flat", prepend-icon="mdi-play-pause") Translate

</template>

<script lang="ts">
import "@/styles/home.scss";

export default {
	data: () => ({
		language: "Czech",
		languages: [
			"Afrikaans",
			"Albanian",
			"Amharic",
			"Arabic",
			"Armenian",
			"Assamese",
			"Azerbaijani",
			"Bashkir",
			"Basque",
			"Belarusian",
			"Bengali",
			"Bosnian",
			"Breton",
			"Bulgarian",
			"Catalan",
			"Chinese",
			"Croatian",
			"Czech",
			"Danish",
			"Dutch",
			"English",
			"Estonian",
			"Faroese",
			"Finnish",
			"French",
			"Galician",
			"Georgian",
			"German",
			"Greek",
			"Gujarati",
			"Haitian Creole",
			"Hausa",
			"Hawaiian",
			"Hebrew",
			"Hindi",
			"Hungarian",
			"Icelandic",
			"Indonesian",
			"Italian",
			"Japanese",
			"Javanese",
			"Kannada",
			"Kazakh",
			"Khmer",
			"Korean",
			"Lao",
			"Latin",
			"Latvian",
			"Lingala",
			"Lithuanian",
			"Luxembourgish",
			"Macedonian",
			"Malagasy",
			"Malay",
			"Malayalam",
			"Maltese",
			"Maori",
			"Marathi",
			"Mongolian",
			"Myanmar",
			"Nepali",
			"Norwegian",
			"Nynorsk",
			"Occitan",
			"Pashto",
			"Persian",
			"Polish",
			"Portuguese",
			"Punjabi",
			"Romanian",
			"Russian",
			"Sanskrit",
			"Serbian",
			"Shona",
			"Sindhi",
			"Sinhala",
			"Slovak",
			"Slovenian",
			"Somali",
			"Spanish",
			"Sundanese",
			"Swahili",
			"Swedish",
			"Tagalog",
			"Tajik",
			"Tamil",
			"Tatar",
			"Telugu",
			"Thai",
			"Tibetan",
			"Turkish",
			"Turkmen",
			"Ukrainian",
			"Urdu",
			"Uzbek",
			"Vietnamese",
			"Welsh",
			"Yiddish",
			"Yoruba",
		],
	}),
};
</script>
