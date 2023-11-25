// Composables
import { createRouter, createWebHistory } from "vue-router";

const routes = [
	{
		path: "/",
		component: () => import("@/views/Home.vue"),
	},
	{
		path: "/viewer",
		component: () => import("@/views/Viewer.vue"),
	},
	{
		path: "/recorder",
		component: () => import("@/views/Recorder.vue"),
	},
];

const router = createRouter({
	history: createWebHistory(),
	routes,
});

export default router;
