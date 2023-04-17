/**
 * main.ts
 *
 * Bootstraps Vuetify and other plugins then mounts the App`
 */

// Components
import App from "./App.vue";
import AudioRecorder from "./components/AudioRecorder.vue";
import TextViewer from "./components/TextViewer.vue";
import EditTextChunk from "./components/EditTextChunk.vue";
import Editor from "@/components/TextEditor.vue";
import SessionList from "@/components/SessionList.vue";

// Composables
import { createApp } from "vue";

// Plugins
import { registerPlugins } from "@/plugins";

const app = createApp(App);
app.component("audio-recorder", AudioRecorder);
app.component("text-viewer", TextViewer);
app.component("edit-text-chunk", EditTextChunk);
app.component("text-editor", Editor);
app.component("session-list", SessionList);

registerPlugins(app);

app.mount("#app");
