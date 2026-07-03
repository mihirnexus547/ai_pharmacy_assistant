class PCMProcessor extends AudioWorkletProcessor {

    process(inputs, outputs, parameters) {

        const input = inputs[0];

        if (!input.length) {
            return true;
        }

        const channel = input[0];

        const pcm = new Int16Array(channel.length);

        for (let i = 0; i < channel.length; i++) {

            let sample = Math.max(
                -1,
                Math.min(1, channel[i])
            );

            pcm[i] = sample * 32767;

        }

        this.port.postMessage(pcm.buffer);

        return true;
    }

}

registerProcessor(
    "pcm-processor",
    PCMProcessor,
);