/**
 * MindFlow Apps SDK - Entry Point
 *
 * Clean ChatGPT Apps SDK integration
 */

// Export main component
export { TaskWidget } from './components/TaskWidget';

// Export SDK
export { AppsSDK, getSDK, AppsSDKError } from './sdk/AppsSDK';
export type { ToolOutput, CallToolOptions, WidgetState } from './sdk/AppsSDK';
