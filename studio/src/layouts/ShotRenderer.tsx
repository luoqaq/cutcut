import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {PreparedClipAsset, ShotSpec} from '../types';
import {VideoSlot} from '../components/VideoSlot';

interface ShotRendererProps {
  shot: ShotSpec;
  clipsMap: Record<string, PreparedClipAsset>;
  durationInFrames: number;
  accentColor: string;
}

export const ShotRenderer: React.FC<ShotRendererProps> = ({
  shot,
  clipsMap,
  durationInFrames,
  accentColor,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const fadeInAlpha =
    shot.transition_in === 'fade'
      ? interpolate(frame, [0, 7], [0, 1], {extrapolateRight: 'clamp'})
      : 1;

  const findSlot = (slotName: string) => {
    const s = shot.clips.find((c) => c.slot === slotName) ?? shot.clips[0];
    const key = `${shot.id}_${s.slot}`;
    return {slotSpec: s, key, asset: clipsMap[key]};
  };

  if (shot.layout === 'cinema_frame') {
    const {slotSpec, key, asset} = findSlot('main');
    const is43 = shot.aspect_ratio === '4:3';
    const frameW = 1008;
    const frameH = is43 ? 756 : 567;
    const topY = is43 ? 470 : 565;

    const enterScale = spring({
      fps,
      frame,
      config: {damping: 24, stiffness: 180, mass: 0.8},
    });
    const containerScale = interpolate(enterScale, [0, 1], [0.985, 1]);

    return (
      <AbsoluteFill style={{opacity: fadeInAlpha}}>
        {/* Warm atmospheric glow behind the cinema frame */}
        {shot.ambient_backdrop !== false && (
          <div
            style={{
              position: 'absolute',
              left: '50%',
              top: topY + frameH / 2,
              width: 960,
              height: frameH + 220,
              transform: 'translate(-50%, -50%)',
              background:
                'radial-gradient(ellipse at center, rgba(243, 201, 139, 0.11) 0%, rgba(160, 120, 75, 0.04) 48%, rgba(0, 0, 0, 0) 76%)',
              pointerEvents: 'none',
            }}
          />
        )}

        <div
          style={{
            position: 'absolute',
            left: (1080 - frameW) / 2,
            top: topY,
            width: frameW,
            transform: `scale(${containerScale.toFixed(4)})`,
          }}
        >
          {/* Micro editorial metadata bar above the frame */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: 14,
              padding: '0 6px',
              fontFamily: '"PingFang SC", "SF Pro Display", sans-serif',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
              <span
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  backgroundColor: accentColor,
                  boxShadow: `0 0 10px ${accentColor}`,
                }}
              />
              <span
                style={{
                  fontSize: 22,
                  fontWeight: 600,
                  color: 'rgba(245, 236, 222, 0.86)',
                  letterSpacing: '0.06em',
                }}
              >
                {shot.badge ?? 'DESK COMPANION'}
              </span>
            </div>
            <span
              style={{
                fontSize: 19,
                fontWeight: 500,
                color: 'rgba(180, 188, 200, 0.58)',
                letterSpacing: '0.1em',
                fontFamily: '"Menlo", "SF Mono", monospace',
              }}
            >
              {shot.camera_meta ?? 'SONY 4K · 25FPS'}
            </span>
          </div>

          <div style={{width: frameW, height: frameH}}>
            {asset ? (
              <VideoSlot
                clipKey={key}
                srcPath={asset.src}
                slotSpec={slotSpec}
                durationInFrames={durationInFrames}
                borderRadius={20}
              />
            ) : null}
          </div>
        </div>
      </AbsoluteFill>
    );
  }

  if (shot.layout === 'triptych') {
    const topItem = findSlot('top');
    const midItem = findSlot('middle');
    const botItem = findSlot('bottom');
    const items = [
      {...topItem, flex: 0.92, delay: 0},
      {...midItem, flex: 1.18, delay: 2},
      {...botItem, flex: 0.92, delay: 4},
    ];

    return (
      <AbsoluteFill style={{opacity: fadeInAlpha}}>
        <div
          style={{
            position: 'absolute',
            left: 36,
            top: 230,
            width: 1008,
            height: 1230,
            display: 'flex',
            flexDirection: 'column',
            gap: 14,
          }}
        >
          {items.map((it, idx) => {
            const p = spring({
              fps,
              frame: Math.max(0, frame - it.delay),
              config: {damping: 22, stiffness: 210},
            });
            const yOff = interpolate(p, [0, 1], [16, 0]);
            const op = interpolate(p, [0, 1], [0.45, 1]);
            return (
              <div
                key={idx}
                style={{
                  flex: it.flex,
                  minHeight: 0,
                  transform: `translateY(${yOff.toFixed(1)}px)`,
                  opacity: op,
                }}
              >
                {it.asset ? (
                  <VideoSlot
                    clipKey={it.key}
                    srcPath={it.asset.src}
                    slotSpec={it.slotSpec}
                    durationInFrames={durationInFrames}
                    borderRadius={16}
                  />
                ) : null}
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
    );
  }

  if (shot.layout === 'split_2') {
    const topItem = findSlot('top');
    const botItem = findSlot('bottom');
    const items = [
      {...topItem, delay: 0},
      {...botItem, delay: 3},
    ];

    return (
      <AbsoluteFill style={{opacity: fadeInAlpha}}>
        <div
          style={{
            position: 'absolute',
            left: 36,
            top: 285,
            width: 1008,
            height: 1110,
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
          }}
        >
          {items.map((it, idx) => {
            const p = spring({
              fps,
              frame: Math.max(0, frame - it.delay),
              config: {damping: 22, stiffness: 200},
            });
            const yOff = interpolate(p, [0, 1], [14, 0]);
            return (
              <div
                key={idx}
                style={{
                  flex: 1,
                  minHeight: 0,
                  transform: `translateY(${yOff.toFixed(1)}px)`,
                }}
              >
                {it.asset ? (
                  <VideoSlot
                    clipKey={it.key}
                    srcPath={it.asset.src}
                    slotSpec={it.slotSpec}
                    durationInFrames={durationInFrames}
                    borderRadius={18}
                  />
                ) : null}
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
    );
  }

  // full_bleed: Tall 3:4 portrait cinema card that preserves safe zones for header & captions
  const {slotSpec, key, asset} = findSlot('main');
  return (
    <AbsoluteFill style={{opacity: fadeInAlpha}}>
      <div
        style={{
          position: 'absolute',
          left: 36,
          top: 235,
          width: 1008,
          height: 1220,
        }}
      >
        {asset ? (
          <VideoSlot
            clipKey={key}
            srcPath={asset.src}
            slotSpec={slotSpec}
            durationInFrames={durationInFrames}
            borderRadius={22}
          />
        ) : null}
      </div>
    </AbsoluteFill>
  );
};
