import React from 'react';
import {Composition} from 'remotion';
import {EditComposition} from './EditComposition';
import activePropsData from './active_props.json';
import {ActiveProps} from './types';

export const RemotionRoot: React.FC = () => {
  const props = activePropsData as unknown as ActiveProps;
  const fps = props.manifest.fps || 30;
  const totalFrames = Math.max(1, Math.round(props.manifest.duration * fps));

  return (
    <>
      <Composition
        id="CutCutEdit"
        component={EditComposition as unknown as React.FC<Record<string, unknown>>}
        durationInFrames={totalFrames}
        fps={fps}
        width={props.manifest.width || 1080}
        height={props.manifest.height || 1920}
        defaultProps={props as unknown as Record<string, unknown>}
      />
    </>
  );
};
