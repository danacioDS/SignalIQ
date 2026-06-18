import { C } from '../components/styles';

export interface RegimeInfo {
  label: string;
  icon: string;
  color: string;
  bgColor: string;
  range: string;
}

export const getRegimeInfo = (ndi: number): RegimeInfo => {
  if (ndi > 2.0) {
    return {
      label: 'Extreme Overheating',
      icon: '🔴',
      color: C.red,
      bgColor: C.redBg,
      range: 'NDI > 2.0',
    };
  } else if (ndi > 1.5) {
    return {
      label: 'Overheating',
      icon: '🟠',
      color: C.orange,
      bgColor: C.orangeBg,
      range: '1.5 < NDI ≤ 2.0',
    };
  } else if (ndi > 0.5) {
    return {
      label: 'Watching',
      icon: '🟡',
      color: C.yellow,
      bgColor: C.yellowBg,
      range: '0.5 < NDI ≤ 1.5',
    };
  } else if (ndi > -0.5) {
    return {
      label: 'Stable',
      icon: '🟢',
      color: C.green,
      bgColor: C.greenBg,
      range: '-0.5 < NDI ≤ 0.5',
    };
  } else if (ndi > -1.5) {
    return {
      label: 'Aligned',
      icon: '🟢',
      color: C.green,
      bgColor: C.greenBg,
      range: '-1.5 < NDI ≤ -0.5',
    };
  } else if (ndi > -2.0) {
    return {
      label: 'Strong Undervalued',
      icon: '🔵',
      color: C.blue,
      bgColor: C.blueBg,
      range: '-2.0 < NDI ≤ -1.5',
    };
  } else {
    return {
      label: 'Extreme Undervalued',
      icon: '🔵',
      color: C.blue,
      bgColor: C.blueBg,
      range: 'NDI ≤ -2.0',
    };
  }
};

export const getRegimeColor = (ndi: number): string => {
  return getRegimeInfo(ndi).color;
};

export const getRegimeBg = (ndi: number): string => {
  return getRegimeInfo(ndi).bgColor;
};

export const getRegimeIcon = (ndi: number): string => {
  return getRegimeInfo(ndi).icon;
};

export const getRegimeLabel = (ndi: number): string => {
  return getRegimeInfo(ndi).label;
};
