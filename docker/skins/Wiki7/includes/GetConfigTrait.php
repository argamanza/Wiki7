<?php
/**
 * Wiki7 - A responsive skin developed for the Star Wiki7 Wiki
 *
 * This file is part of Wiki7.
 *
 * Wiki7 is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Wiki7 is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Wiki7.  If not, see <https://www.gnu.org/licenses/>.
 *
 * @file
 * @ingroup Skins
 */

declare( strict_types=1 );

namespace MediaWiki\Skins\Wiki7;

use MediaWiki\Config\ConfigException;
use MediaWiki\Output\OutputPage;

trait GetConfigTrait {

	/**
	 * getConfig() wrapper to catch exceptions.
	 * Returns null on exception
	 *
	 * @param string $key
	 * @param OutputPage|null $out
	 * @return mixed|null
	 * @see SkinTemplate::getConfig()
	 */
	protected function getConfigValue( $key, $out = null ) {
		if ( isset( $this->out ) ) {
			$out = $this->out;
		}

		if ( is_callable( [ $this, 'getOutput' ] ) ) {
			$out = $this->getOutput();
		}

		try {
			$value = $out->getConfig()->get( $key );
		} catch ( ConfigException $e ) {
			$value = null;
		}

		return $value;
	}
}
