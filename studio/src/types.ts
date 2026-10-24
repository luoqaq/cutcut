export type LayoutKind = 'cinema_frame' | 'triptych' | 'split_2' | 'full_bleed';

export interface ClipSlotSpec {
  slot: 'main' | 'top' | 'middle' | 'bottom';
  source: string;
  start: number;
  speed?: number;
  crop_focus?: [number, number];
  zoom_from?: number;
  zoom_to?: number;
  label?: string;
  keep_audio?: boolean;
  audio_gain_db?: number;
}

export interface ShotSpec {
  id: string;
  index?: number;
  layout: LayoutKind;
  duration: number;
  timeline_start?: number;
  timeline_end?: number;
  aspect_ratio?: '16:9' | '4:3';
  ambient_backdrop?: boolean;
  transition_in?: 'none' | 'fade';
  badge?: string;
  camera_meta?: string;
  clips: ClipSlotSpec[];
  note?: string;
}

export interface CaptionSpec {
  id: string;
  start: number;
  end: number;
  text: string;
  highlight?: string;
  subtext?: string;
  position?: 'bottom' | 'lower_mid';
}

export interface ThemeSpec {
  bg_color?: string;
  accent_color?: string;
  header_tag?: string;
  header_subtitle?: string;
}

export interface EditSpec {
  project_id: string;
  title: string;
  output_filename?: string;
  width: number;
  height: number;
  fps: number;
  cover_time?: number;
  theme?: ThemeSpec;
  shots: ShotSpec[];
  captions: CaptionSpec[];
}

export interface PreparedClipAsset {
  src: string;
  width: number;
  height: number;
  duration: number;
}

export interface ActiveProps {
  spec: EditSpec;
  manifest: {
    duration: number;
    fps: number;
    width: number;
    height: number;
    masterAudioSrc: string;
    clips: Record<string, PreparedClipAsset>;
  };
}
