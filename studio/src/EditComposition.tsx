import React from 'react';
import {AbsoluteFill, Audio, Sequence, staticFile, useVideoConfig} from 'remotion';
import {ActiveProps} from './types';
import {ShotRenderer} from './layouts/ShotRenderer';
import {CaptionOverlay, EditorialHeader} from './components/Overlays';

export const EditComposition: React.FC<ActiveProps> = ({spec, manifest}) => {
  const {fps} = useVideoConfig();
  const bgColor = spec.theme?.bg_color ?? '#0A0B0E';
  const accentColor = spec.theme?.accent_color ?? '#F3C98B';

  let cursorFrames = 0;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: bgColor,
        backgroundImage:
          'radial-gradient(circle at 50% 18%, rgba(42, 36, 30, 0.42) 0%, rgba(10, 11, 14, 1) 68%)',
        overflow: 'hidden',
      }}
    >
      {manifest.masterAudioSrc ? (
        <Audio src={staticFile(manifest.masterAudioSrc)} volume={1} />
      ) : null}

      {spec.shots.map((shot) => {
        const startFrame = cursorFrames;
        const durFrames = Math.max(1, Math.round(shot.duration * fps));
        cursorFrames += durFrames;

        return (
          <Sequence
            key={shot.id}
            from={startFrame}
            durationInFrames={durFrames}
            name={`${shot.id}_${shot.layout}`}
          >
            <ShotRenderer
              shot={shot}
              clipsMap={manifest.clips}
              durationInFrames={durFrames}
              accentColor={accentColor}
            />
          </Sequence>
        );
      })}

      <EditorialHeader theme={spec.theme} />
      <CaptionOverlay captions={spec.captions} accentColor={accentColor} />
    </AbsoluteFill>
  );
};
