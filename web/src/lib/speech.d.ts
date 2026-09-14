interface MentorSpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

interface MentorSpeechRecognitionResult {
  readonly length: number;
  item(index: number): MentorSpeechRecognitionAlternative;
  [index: number]: MentorSpeechRecognitionAlternative;
}

interface MentorSpeechRecognitionResultList {
  readonly length: number;
  item(index: number): MentorSpeechRecognitionResult;
  [index: number]: MentorSpeechRecognitionResult;
}

interface MentorSpeechRecognitionEvent extends Event {
  resultIndex: number;
  results: MentorSpeechRecognitionResultList;
}

interface MentorSpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onresult: ((event: MentorSpeechRecognitionEvent) => void) | null;
  onend: (() => void) | null;
  onerror: ((event: Event) => void) | null;
  start(): void;
  stop(): void;
}

type MentorSpeechRecognitionCtor = { new (): MentorSpeechRecognition };
