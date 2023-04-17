async function main() {
	const context = new AudioContext();
	const microphone = await navigator.mediaDevices.getUserMedia({
		audio: true,
	});

	const source = context.createMediaStreamSource(microphone);

	await context.audioWorklet.addModule("/recorder.worklet.js");
	const recorder = new AudioWorkletNode(context, "recorder.worklet");

	source.connect(recorder).connect(context.destination);

	recorder.port.onmessage = (e: { data: Float32Array }) => {
		fetch("http://slt.ufal.cuni.cz:5003/submit_audio_chunk", {
			method: "POST", // *GET, POST, PUT, DELETE, etc.
			mode: "no-cors", // no-cors, *cors, same-origin
			cache: "no-cache", // *default, no-cache, reload, force-cache, only-if-cached
			credentials: "same-origin", // include, *same-origin, omit
			headers: {
				"Content-Type": "application/json",
				// 'Content-Type': 'application/x-www-form-urlencoded',
			},
			redirect: "follow", // manual, *follow, error
			referrerPolicy: "no-referrer", // no-referrer, *no-referrer-when-downgrade, origin, origin-when-cross-origin, same-origin, strict-origin, strict-origin-when-cross-origin, unsafe-url
			body: JSON.stringify({ chunk: e.data, timestamp: 0 }), // body data type must match "Content-Type" header
		});
	};
}

function convertFloat32To16BitPCM(input: Float32Array): Int16Array {
	const output = new Int16Array(input.length);

	for (let i = 0; i < input.length; i++) {
		const s = Math.max(-1, Math.min(1, input[i]));
		// output[i] = s < 0 ? s * 32768 : s * 32767;
		// output[i] = s * 32400;
		output[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
	}
	return output;
}

export { main };
