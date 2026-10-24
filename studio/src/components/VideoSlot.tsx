import React from 'react';
import {interpolate, OffthreadVideo, staticFile, useCurrentFrame} from 'remotion';
import {ClipSlotSpec} from '../types';

interface VideoSlotProps {
  clipKey: string;
  srcPath: string;
  slotSpec: ClipSlotSpec;
  durationInFrames: number;
  borderRadius?: number;
}

export const VideoSlot: React.FC<VideoSlotProps> = ({
  srcPath,
  slotSpec,
  durationInFrames,
  borderRadius = 16,
}) => {
  const frame = useCurrentFrame();
  const zoomFrom = slotSpec.zoom_from ?? 1.0;
  const zoomTo = slotSpec.zoom_to ?? 1.04;
  const scale = interpolate(frame, [0, Math.max(1, durationInFrames - 1)], [zoomFrom, zoomTo], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const [cx, cy] = slotSpec.crop_focus ?? [0.5, 0.5];

  return (
    <div
      style={{
        position: 'relative',
        width: '100%',
        height: '100%',
        overflow: 'hidden',
        borderRadius,
        backgroundColor: '#121318',
        border: '1px solid rgba(243, 201, 139, 0.16)',
        boxShadow: '0 24px 68px rgba(0, 0, 0, 0.68)',
      }}
    >
      <OffthreadVideo
        src={staticFile(srcPath)}
        muted
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          objectPosition: `${(cx * 100).toFixed(1)}% ${(cy * 100).toFixed(1)}%`,
          transform: `scale(${scale.toFixed(4)})`,
          transformOrigin: `${(cx * 100).toFixed(1)}% ${(cy * 100).toFixed(1)}%`,
        }}
      />

      {/* Subtle cinematic inner vignette */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(circle at center, rgba(0,0,0,0) 64%, rgba(0,0,0,0.28) 100%)',
          pointerEvents: 'none',
        }}
      />

      {slotSpec.label ? (
        <div
          style={{
            position: 'absolute',
            left: 18,
            bottom: 16,
            padding: '6px 14px',
            borderRadius: 999,
            backgroundColor: 'rgba(12, 13, 18, 0.68)',
            border: '1px solid rgba(243, 201, 139, 0.28)',
            color: '#F5E6CC',
            fontSize: 22,
            fontWeight: 600,
            letterSpacing: '0.04em',
            fontFamily: '"PingFang SC", "Hiragino Sans GB", sans-serif',
          }}
        >
          {slotSpec.label}
        </div>
      ) : null}
    </div>
  );
};
