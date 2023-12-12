export interface SourceString {
    string: string;
    active: boolean;
}

export interface DictEntry {
    source_strings: SourceString[];
    to: string;
    version: number;
    active: boolean;
    locked: boolean;
    // deleted: boolean;
}

export type Dict = DictEntry[];
