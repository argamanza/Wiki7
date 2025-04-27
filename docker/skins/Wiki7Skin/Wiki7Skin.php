<?php
/**
 * SkinTemplate class for Wiki7Skin skin
 *
 * @ingroup Skins
 */
class SkinWiki7Skin extends SkinMustache {
    /**
     * Extends the getTemplateData function to add custom data
     * for the mustache template
     *
     * @return array Data for template
     */
    public function getTemplateData() {
        $data = parent::getTemplateData();
        
        // Add custom data here
        $data['skin-name'] = 'wiki7skin';
        $data['msg-tagline'] = $this->msg( 'tagline' )->text();
        
        // Add team-specific information
        $data['team-name'] = 'Hapoel Beer Sheva FC';
        $data['team-colors'] = 'red-white'; // Can be used for styling
        $data['team-nickname'] = 'The Camels';
        
        return $data;
    }
    
    /**
     * @inheritDoc
     */
    public function getDefaultModules() {
        $modules = parent::getDefaultModules();
        // Add any additional modules here
        return $modules;
    }
}