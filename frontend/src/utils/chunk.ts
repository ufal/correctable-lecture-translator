export type TimeStamp = number;
export type Version = number;
export type AudioData = Float32Array;

export interface TextChunkData {
	version: Version;
	text: string;
}

export interface TextChunk {
	timestamp: TimeStamp;
	version: Version;
	text: string;
}

export interface TextChunksUpdate {
	textChunks: TextChunk[];
	versions: TextChunkVersions;
}

export type TextChunkVersions = { [key: TimeStamp]: Version };

export interface AudioChunk {
	timestamp: TimeStamp;
	chunk: AudioData;
}
