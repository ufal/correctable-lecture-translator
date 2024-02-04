// Composables
import { createRouter, createWebHistory } from "vue-router";

const routes = [
	{
		path: "/",
		component: () => import("@/views/Viewing.vue"),

	},
	{
		path: "/record",
		component: () => import("@/views/Recording.vue"),
	},
];

const router = createRouter({
	history: createWebHistory(),
	routes,
});


export default router;
