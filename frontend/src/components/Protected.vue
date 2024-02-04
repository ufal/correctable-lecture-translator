<template>
	<div>
		<div class="container text-center">
			<h2>Please enter password to access this page.</h2>
			<form v-on:submit.prevent="validateBeforeSubmit">
					<label class="custom-label control-label">Password:</label>
					<input
						class="form-control password-field"
						type="password"
						name="password"
						v-model.trim="password"
					/>
					<span class="error help-block"></span>
				<div class="text-danger" v-if="error"><p>Incorrect password.</p></div>
				<button class="password-btn btn-primary" type="submit">Submit</button>
			</form>
		</div>
	</div>
</template>

<style scoped></style>

<script lang="ts">
import { defineComponent } from "vue";
import { useCookies } from "vue3-cookies";
import "@/styles/protected.scss";

export default defineComponent({
	props: {
		auth: {
			type: Object,
			required: true,
		},
	},
	data() {
		return {
			password: null,
			error: false,
		};
	},
	methods: {
		validateBeforeSubmit() {
			if (this.password === "VelmySylneHeslo23") {
				const { cookies } = useCookies();
				cookies.set("password", this.password);
				this.auth.loggedIn = true;
			} else {
				this.auth.loggedIn = false;
				this.error = true;
			}
		},
	},
	mounted() {
		const { cookies } = useCookies();
		if (cookies.get("password") === "VelmySylneHeslo23") {
			this.auth.loggedIn = true;
		}
	},
});
</script>
