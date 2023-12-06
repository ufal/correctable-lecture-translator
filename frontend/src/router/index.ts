// Composables
import { createRouter, createWebHistory } from "vue-router";

const routes = [
	{
		path: "/",
		component: () => import("@/views/Home.vue"),
	},
	{
		path: "/viewing",
		component: () => import("@/views/Viewing.vue"),
	},
	{
		path: "/recording",
		component: () => import("@/views/Recording.vue"),
	},
];

const router = createRouter({
	history: createWebHistory(),
	routes,
});

export default router;
