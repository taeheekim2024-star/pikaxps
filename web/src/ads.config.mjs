// Advertising / sponsorship slot configuration for the documentation site.
//
// The site ships with NO ads. This file only reserves the place so that an ad or sponsor
// network can be switched on later without touching the layout:
//
//   provider: 'none'        – nothing is rendered (default)
//             'ethicalads'  – EthicalAds text slot (privacy-friendly, no cookies):
//                             sign up at https://www.ethicalads.io/, then fill in the
//                             publisher id below.
//             'custom'      – render the HTML in `customHtml` (e.g. a sponsor banner).
//
// Whatever the provider, the project notice bar (notice.json) keeps working independently.
export const AD = {
  provider: 'none',
  ethicaladsPublisher: '',
  customHtml: '',
};
