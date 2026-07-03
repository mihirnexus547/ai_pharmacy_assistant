const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");

const status = document.getElementById("status");
const log = document.getElementById("log");

let socket;
let audioContext;
let source;
let processor;

startBtn.onclick = async () => {

    status.innerHTML = "Connecting...";

    socket = new WebSocket(
        "wss://fretful-plus-vixen.ngrok-free.dev/ws/audio"
    );

    socket.binaryType = "arraybuffer";

    socket.onopen = async () => {

        status.innerHTML = "Listening...";

        const stream =
            await navigator.mediaDevices.getUserMedia({
                audio: true,
            });

        audioContext = new AudioContext({
            sampleRate: 16000,
        });

        await audioContext.audioWorklet.addModule(
            "/static/processor.js"
        );

        source = audioContext.createMediaStreamSource(stream);

        processor = new AudioWorkletNode(
            audioContext,
            "pcm-processor"
        );

        processor.port.onmessage = (event) => {

            if (socket.readyState === WebSocket.OPEN) {

                socket.send(event.data);

            }

        };

        source.connect(processor);
        processor.connect(audioContext.destination);

    };

    socket.onmessage = async (event) => {

        if (typeof event.data === "string") {

            const message = JSON.parse(event.data);

            if (message.type === "transcript") {

                status.innerHTML =
                    "You: " + message.text;

            }

            if (message.type === "assistant") {

                log.innerHTML +=
                    "\nAssistant: " +
                    message.text +
                    "\n";

            }

            return;

        }

        console.log(
            "Received audio:",
            event.data.byteLength,
            "bytes"
        );

        const blob = new Blob(
            [event.data],
            {
                type: "audio/mpeg",
            }
        );

        const url = URL.createObjectURL(blob);

        const audio = new Audio(url);

        try {

            await audio.play();

        } catch (err) {

            console.error(err);

        }

    };

    socket.onerror = (err) => {

        console.error(err);

        status.innerHTML = "WebSocket Error";

    };

    socket.onclose = () => {

        status.innerHTML = "Disconnected";

    };

};

stopBtn.onclick = async () => {

    if (processor)
        processor.disconnect();

    if (source)
        source.disconnect();

    if (audioContext)
        await audioContext.close();

    if (socket)
        socket.close();

    status.innerHTML = "Stopped";

};