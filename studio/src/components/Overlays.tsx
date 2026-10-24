import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {CaptionSpec, ThemeSpec} from '../types';

export const EditorialHeader: React.FC<{theme?: ThemeSpec}> = ({theme}) => {
  const accent = theme?.accent_color ?? '#F3C98B';
  const tag = theme?.header_tag ?? 'DESK VLOG · 陪班日常';
  const sub = theme?.header_subtitle ?? 'CODING WITH MY FLUFFY COWORKERS';

  return (
    <div
      style={{
        position: 'absolute',
        top: 118,
        left: 0,
        right: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 8,
        pointerEvents: 'none',
      }}
    >
      <div
        style={{
          padding: '6px 20px',
          borderRadius: 999,
          backgroundColor: 'rgba(243, 201, 139, 0.10)',
          border: '1px solid rgba(243, 201, 139, 0.26)',
          color: accent,
          fontSize: 23,
          fontWeight: 600,
          letterSpacing: '0.12em',
          fontFamily: '"PingFang SC", "Hiragino Sans GB", sans-serif',
        }}
      >
        {tag}
      </div>
      <div
        style={{
          fontSize: 16,
          fontWeight: 500,
          color: 'rgba(210, 216, 226, 0.46)',
          letterSpacing: '0.22em',
          fontFamily: '"SF Pro Display", "Helvetica Neue", sans-serif',
        }}
      >
        {sub}
      </div>
    </div>
  );
};

const renderHighlightedText = (text: string, highlight: string | undefined, accentColor: string) => {
  if (!highlight || !text.includes(highlight)) {
    return <span>{text}</span>;
  }
  const idx = text.indexOf(highlight);
  const before = text.slice(0, idx);
  const after = text.slice(idx + highlight.length);
  return (
    <>
      <span>{before}</span>
      <span
        style={{
          color: accentColor,
          padding: '0 4px',
          textShadow: '0 2px 18px rgba(243, 201, 139, 0.35)',
        }}
      >
        {highlight}
      </span>
      <span>{after}</span>
    </>
  );
};

export const CaptionOverlay: React.FC<{
  captions: CaptionSpec[];
  accentColor: string;
}> = ({captions, accentColor}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const currentTime = frame / fps;

  const active = captions.find((c) => currentTime >= c.start && currentTime <= c.end);
  if (!active) return null;

  const localFrame = Math.max(0, Math.round((currentTime - active.start) * fps));
  const remainingFrames = Math.max(0, Math.round((active.end - currentTime) * fps));

  const pop = spring({
    fps,
    frame: localFrame,
    config: {damping: 20, stiffness: 240, mass: 0.7},
  });
  const yTranslate = interpolate(pop, [0, 1], [14, 0]);
  const fadeOut = interpolate(remainingFrames, [0, 5], [0, 1], {extrapolateRight: 'clamp'});
  const opacity = Math.min(pop, fadeOut);

  const bottomOffset = active.position === 'lower_mid' ? 355 : 275;

  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <div
        style={{
          position: 'absolute',
          left: 44,
          right: 44,
          bottom: bottomOffset,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 14,
          opacity,
          transform: `translateY(${yTranslate.toFixed(1)}px)`,
        }}
      >
        <div
          style={{
            fontSize: 48,
            fontWeight: 700,
            color: '#FAF7F2',
            textAlign: 'center',
            lineHeight: 1.28,
            letterSpacing: '0.03em',
            fontFamily: '"PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif',
            textShadow: '0 4px 18px rgba(0, 0, 0, 0.88), 0 1px 3px rgba(0, 0, 0, 0.95)',
          }}
        >
          {renderHighlightedText(active.text, active.highlight, accentColor)}
        </div>

        {active.subtext ? (
          <div
            style={{
              padding: '7px 22px',
              borderRadius: 999,
              backgroundColor: 'rgba(18, 20, 26, 0.78)',
              border: '1px solid rgba(243, 201, 139, 0.24)',
              fontSize: 28,
              fontWeight: 500,
              color: '#E6D8C3',
              letterSpacing: '0.05em',
              fontFamily: '"PingFang SC", "Hiragino Sans GB", sans-serif',
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.45)',
            }}
          >
            {active.subtext}
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};
