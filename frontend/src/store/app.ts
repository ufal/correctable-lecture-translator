// Utilities
import { defineStore } from "pinia";

export const useAppStore = defineStore("app", {
	state: () => ({ count: 0, name: "Eduardo" }),
	getters: {
		doubleCount: (state) => state.count * 2,
	},
	actions: {
		increment() {
			this.count++;
		},
	},
});
