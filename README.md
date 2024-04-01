# Coletra
A system for live lecture translation (speech to text) where the audience can easily provide corrections. Built by two Charles University students Marko Čechovič and Jakub Parada under supervision of doc. RNDr. Ondřej Bojar, Ph.D. Version 2 of the project under the name of Coletra is released thanks to the MFF CUNI Student faculty grant programe which provided funds.

## Usage

### Recorder
After succesfull setup, go to `API_URL/record` (the one given to the frontend container), write new unique session name and click the plus button. This will create a new recording session. Then press the "microphone" button to start sending audio from your system's primary microphone (audio input device). You can pause and then resume the recording by clicking the "pause" button and again the "microphone" button.

### Viewer
On the main page `API_URL/` (the one given to the frontend container) in the top right input field, put in the name of the session created at the `/recorder` endpoint and click the "play" button which will make.tour client start fetching the text (and correction rules) from the server. This can be paused by clicking on the "pause" button that should be visible in place of the "play" button while your client is actively getting and sending updates to the server.

There are 3 viewing modes:
- "Presentstion" view which is meant for displaying at large screens, projectors etc.
- "Normal" view meant eg. for mobiles and laptops.
- "Editing" view where is the editing UI as well as the correction rules.

### Editor
In the editing UI, everyone can access chunks of the transcriptions/translations and make editions. If there are repeating misstakes, the global editing rules can be created to fix the problematic texts every time they appear (only newly "generated" text is mosified by the existing rules, which meams that misstakes made before creation of a rule needs to be fixed manually). The rules are applied in the order they are displayed in the UI from top to bottom. Each rule can be moved, temporarily disabled or removed entirely.
